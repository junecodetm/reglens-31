"""Response models for the RegLens read API — the single source of truth for its shape.

Inputs: the validated pipeline records (``reglens.extract.records``,
``reglens.currency``, ``reglens.structure``). Outputs: typed projections that
:mod:`reglens.api.spec` turns into an OpenAPI 3.1 document and
:mod:`reglens.store.export_api` materializes as static JSON.

Failure mode: pydantic ``ValidationError`` — a payload that does not match the
published contract is never written or served.

One schema, one dataset, one transport. There is deliberately no server: the API
is the same pre-computed static export the site itself reads, so it cannot drift
from the pages, cannot cost anything to run, and cannot become a live dependency
for a reviewer (CLAUDE.md section 21). ``tests/test_api_contract.py`` asserts the
materialized files agree with the site's own data files.
"""

from typing import Final, Literal

from pydantic import BaseModel, Field

API_VERSION: Final = "v1"
"""Path segment and contract version. A breaking change requires a new segment."""


class RunProvenance(BaseModel):
    """Published run metadata for one claim."""

    model_tag: str = Field(description="Pinned model identifier, e.g. qwen3:8b.")
    prompt_sha256: str = Field(description="SHA-256 of the system + user prompt template.")
    input_sha256: str = Field(
        description="SHA-256 of the bounded document text supplied to the chunking pipeline."
    )
    temperature: float
    runtime: str = Field(
        description=(
            "Inference runtime and version, e.g. ollama/0.30.7. 'unknown' where the "
            "producing run predates this field; it is never backfilled."
        )
    )
    chunk_plan_sha256: str = Field(
        description=(
            "Identity of the chunk sequence the model was shown. The model reads one "
            "chunk at a time, so different boundaries are a different run."
        )
    )


class Claim(BaseModel):
    """One extracted obligation and the provenance gate's verdict on it."""

    claim_id: str
    document_number: str
    quote: str = Field(description="The claimed verbatim span, exactly as the model returned it.")
    obligation_type: str
    affected_party: str
    summary: str = Field(description="Model-written. Not verbatim, and not gate-verified.")
    effective_date: str | None
    accepted: bool = Field(description="True iff the quote verified against the source text.")
    start: int | None = Field(
        description="Character offset into the source text; null if rejected."
    )
    end: int | None
    rejection_reason: str | None
    run: RunProvenance


class DocumentSummary(BaseModel):
    """One corpus document and how much of it was extracted."""

    document_number: str
    document_title: str
    document_url: str
    document_sha256: str
    accepted_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    total_chars: int = Field(ge=0, description="Characters in the full source text.")
    extracted_chars: int = Field(
        ge=0, description="Characters actually given to the model; may be less than total_chars."
    )


class DocumentDetail(DocumentSummary):
    """A document together with every claim extracted from it."""

    claims: list[Claim]


class DocumentCollection(BaseModel):
    """Every document with an extraction record in the published sample."""

    count: int = Field(ge=0)
    documents: list[DocumentSummary]


class ClaimPage(BaseModel):
    """One materialized page of claims.

    Pagination is materialized rather than query-driven because this API is
    served as static files (see docs/ARCHITECTURE.md): ``next`` is a URL, not a
    cursor to be constructed.
    """

    page: int = Field(ge=1)
    page_count: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    next: str | None = Field(description="Path of the next page, or null on the last page.")
    claims: list[Claim]


class SectionSummary(BaseModel):
    """One CFR section span located in the committed part text."""

    part: int
    designation: str
    heading: str
    start: int
    end: int


class SectionCollection(BaseModel):
    count: int = Field(ge=0)
    sections: list[SectionSummary]


class CurrencyPart(BaseModel):
    """Amendment currency for one in-scope part, against the pinned snapshot date."""

    part: int
    census_count: int = Field(ge=0, description="Sections eCFR's structure index lists.")
    amended_since_snapshot: int = Field(ge=0)


class Currency(BaseModel):
    """Whether the pinned corpus has drifted from the live regulation."""

    snapshot_date: str = Field(description="The point-in-time date the corpus is pinned to.")
    total_sections: int = Field(ge=0)
    total_amended_since_snapshot: int = Field(ge=0)
    parts: list[CurrencyPart]
    source_urls: list[str] = Field(description="The eCFR endpoints this was derived from.")


class Metrics(BaseModel):
    """Evaluation metrics, carrying the provisional label verbatim.

    ``provisional_label`` is a required field in the published contract.
    """

    provisional_label: str
    precision: float
    recall: float
    f1: float
    citation_fidelity: float
    n_provisions: int = Field(ge=0)
    n_documents: int = Field(ge=0)
    adjudicated_count: int = Field(ge=0)
    total_gold_count: int = Field(ge=0)


class Corpus(BaseModel):
    """What was extracted, out of what was in scope."""

    data_as_of: str
    documents_extracted: int = Field(ge=0)
    documents_in_scope: int = Field(ge=0)
    chars_extracted: int = Field(ge=0)
    chars_in_scope: int = Field(ge=0)
    max_document_chars: int = Field(
        ge=0,
        description=(
            "Per-document extraction cap for Federal Register documents. The CFR "
            "part texts are uncapped; a document's own total_chars/extracted_chars "
            "record what the cap actually cost it."
        ),
    )
    accepted_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    model_tags: list[str]


class ServiceIndex(BaseModel):
    """Entry point: what this API is, what it is not, and where everything lives."""

    name: Literal["RegLens-31 read API"] = "RegLens-31 read API"
    api_version: str = API_VERSION
    description: str
    disclaimer: str
    corpus: Corpus
    links: dict[str, str] = Field(description="Relation name to path, for every endpoint.")
