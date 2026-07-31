"""Materialize the read API as static JSON under ``web/public/api/v1``.

Inputs: the artifacts already written to ``web/public/data`` by
:mod:`reglens.store.export_web`. Outputs: one JSON file per endpoint, validated
against :mod:`reglens.api.schemas`, plus the OpenAPI document. Failure mode: a
missing input raises ``FileNotFoundError`` and a payload that does not satisfy
its model raises ``ValidationError`` — a partial or unvalidated API is never
published.

Deriving the API from the site's own exported files rather than from
``data/processed`` is deliberate: it makes "the API serves what the pages show"
a structural fact instead of a claim two code paths have to keep agreeing on.

Everything here is a pure function of committed inputs — no clock reads, sorted
iteration order — so re-running the exporter is byte-identical and the CI replay
guard can diff the result.
"""

import json
import shutil
from pathlib import Path
from typing import Final

from pydantic import BaseModel

from reglens.api.schemas import (
    API_VERSION,
    Claim,
    ClaimPage,
    Corpus,
    Currency,
    CurrencyPart,
    DocumentCollection,
    DocumentDetail,
    DocumentSummary,
    Metrics,
    RunProvenance,
    SectionCollection,
    SectionSummary,
    ServiceIndex,
)
from reglens.api.spec import DISCLAIMER, build_openapi
from reglens.currency import CurrencyExport
from reglens.extract.records import DocumentExtraction, load_extractions
from reglens.structure import SectionsExport

API_ROOT: Final = Path("public") / "api" / API_VERSION
CLAIMS_PAGE_SIZE: Final = 100
"""Claims per materialized page.

Pagination is materialized because these are files, not query results: the page
size is fixed at export time and ``next`` is a path a client can follow without
constructing anything.
"""


def _write(path: Path, model: BaseModel) -> None:
    """Write one validated model as pretty JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")


def _claims_of(extraction: DocumentExtraction) -> list[Claim]:
    """Project one document's persisted claims onto the published claim shape."""
    return [
        Claim(
            claim_id=claim.claim_id,
            document_number=claim.document_number,
            quote=claim.quote,
            obligation_type=claim.obligation_type,
            affected_party=claim.affected_party,
            summary=claim.summary,
            effective_date=claim.effective_date,
            accepted=claim.accepted,
            start=claim.start,
            end=claim.end,
            rejection_reason=claim.rejection_reason,
            run=RunProvenance(
                model_tag=claim.run.model_tag,
                prompt_sha256=claim.run.prompt_sha256,
                input_sha256=claim.run.input_sha256,
                temperature=claim.run.temperature,
                runtime=claim.run.runtime,
                chunk_plan_sha256=claim.run.chunk_plan_sha256,
            ),
        )
        for claim in extraction.claims
    ]


def _summary(extraction: DocumentExtraction) -> DocumentSummary:
    return DocumentSummary(
        document_number=extraction.document_number,
        document_title=extraction.document_title,
        document_url=extraction.document_url,
        document_sha256=extraction.document_sha256,
        accepted_count=extraction.accepted_count,
        rejected_count=extraction.rejected_count,
        total_chars=extraction.total_chars,
        extracted_chars=extraction.extracted_chars,
    )


def _currency(export: CurrencyExport) -> Currency:
    return Currency(
        snapshot_date=export.snapshot_date,
        total_sections=export.total_sections,
        total_amended_since_snapshot=export.total_amended_since_snapshot,
        parts=[
            CurrencyPart(
                part=part.part,
                census_count=part.census_count,
                amended_since_snapshot=part.amended_since_snapshot,
            )
            for part in export.parts
        ],
        source_urls=sorted({source.url for source in export.sources}),
    )


def _sections(export: SectionsExport) -> SectionCollection:
    sections = [
        SectionSummary(
            part=part.part,
            designation=section.designation,
            heading=section.heading,
            start=section.start,
            end=section.end,
        )
        for part in export.parts
        for section in part.sections
    ]
    return SectionCollection(count=len(sections), sections=sections)


def _metrics(payload: dict[str, object]) -> Metrics:
    """Project the eval report, keeping the provisional label attached to the numbers."""
    return Metrics.model_validate(payload)


def _claim_pages(claims: list[Claim]) -> list[ClaimPage]:
    """Split claims into fixed-size pages, each naming the path of the next."""
    pages = [
        claims[start : start + CLAIMS_PAGE_SIZE]
        for start in range(0, len(claims), CLAIMS_PAGE_SIZE)
    ] or [[]]
    return [
        ClaimPage(
            page=number,
            page_count=len(pages),
            page_size=CLAIMS_PAGE_SIZE,
            total=len(claims),
            next=(
                f"/api/{API_VERSION}/claims/page-{number + 1}.json" if number < len(pages) else None
            ),
            claims=page,
        )
        for number, page in enumerate(pages, start=1)
    ]


def export_api_data(web_dir: Path) -> Path:
    """Write every endpoint under ``web/public/api/v1`` and return that directory.

    The tree is removed first, so a document dropped from the sample cannot leave
    a stale file behind claiming to be current. Removal failures propagate rather
    than being swallowed: a tree that could not be cleared is exactly the case
    that would leave such a file.
    """
    data_dir = web_dir / "public" / "data"
    api_dir = web_dir / API_ROOT
    if api_dir.exists():
        shutil.rmtree(api_dir)

    extractions = sorted(
        load_extractions(data_dir / "claims.json"), key=lambda item: item.document_number
    )
    corpus = Corpus.model_validate(json.loads((data_dir / "site.json").read_text()))
    currency = _currency(
        CurrencyExport.model_validate_json((data_dir / "currency.json").read_text())
    )
    sections = _sections(
        SectionsExport.model_validate_json((data_dir / "sections.json").read_text())
    )
    metrics = _metrics(json.loads((data_dir / "eval.json").read_text()))

    for extraction in extractions:
        _write(
            api_dir / "documents" / f"{extraction.document_number}.json",
            DocumentDetail(**_summary(extraction).model_dump(), claims=_claims_of(extraction)),
        )
    _write(
        api_dir / "documents.json",
        DocumentCollection(
            count=len(extractions), documents=[_summary(item) for item in extractions]
        ),
    )

    claims = [claim for extraction in extractions for claim in _claims_of(extraction)]
    pages = _claim_pages(claims)
    for page in pages:
        _write(api_dir / "claims" / f"page-{page.page}.json", page)

    _write(api_dir / "sections.json", sections)
    _write(api_dir / "currency.json", currency)
    _write(api_dir / "metrics.json", metrics)
    _write(
        api_dir / "index.json",
        ServiceIndex(
            description=(
                "Static, read-only JSON for every artifact the RegLens-31 site renders: "
                "provenance-gated regulatory obligations, the CFR section structure they "
                "were extracted from, corpus currency against eCFR, and evaluation metrics."
            ),
            disclaimer=DISCLAIMER,
            corpus=corpus,
            links={
                "claims": f"/api/{API_VERSION}/claims/page-1.json",
                "currency": f"/api/{API_VERSION}/currency.json",
                "documents": f"/api/{API_VERSION}/documents.json",
                "metrics": f"/api/{API_VERSION}/metrics.json",
                "openapi": f"/api/{API_VERSION}/openapi.json",
                "sections": f"/api/{API_VERSION}/sections.json",
                "self": f"/api/{API_VERSION}/index.json",
            },
        ),
    )
    (api_dir / "openapi.json").write_text(
        json.dumps(build_openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return api_dir
