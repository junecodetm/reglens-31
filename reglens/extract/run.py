"""Extraction pipeline: snapshots -> chunks -> LLM -> provenance gate -> records.

Inputs: content-addressed snapshots under ``data/raw/``. Outputs: a list of
:class:`DocumentExtraction` (accepted AND rejected claims — rejections are
counted, never hidden). Failure mode: a document with no metadata/text pair is
skipped with nothing recorded; a claim that cannot be verified is recorded as
rejected (fail-closed, see ``reglens.provenance``).
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

import httpx
import structlog
from pydantic import ValidationError

from reglens.config import Settings
from reglens.extract.chunk import chunk_text
from reglens.extract.llm import LLMProvider, input_sha256
from reglens.extract.records import ClaimRecord, DocumentExtraction, claim_id
from reglens.extract.schema import ExtractedObligation, RunMeta
from reglens.ingest.snapshot import iter_snapshots
from reglens.provenance import verify_span


class DocumentPair(NamedTuple):
    """A source document's metadata snapshot joined to its raw-text snapshot."""

    document_number: str
    title: str
    url: str
    text_sha256: str
    text: str


def discover_documents(data_dir: Path) -> list[DocumentPair]:
    """Pair metadata and raw-text snapshots by document number, sorted for determinism."""
    metadata: dict[str, dict[str, str]] = {}
    texts: dict[str, tuple[str, str]] = {}
    for snapshot_dir, manifest in iter_snapshots(data_dir / "raw"):
        stem = Path(manifest.filename).stem
        payload = (snapshot_dir / manifest.filename).read_bytes()
        if manifest.content_type == "application/json":
            metadata[stem] = json.loads(payload)
        elif manifest.content_type == "text/plain":
            texts[stem] = (manifest.sha256, payload.decode())
    pairs: list[DocumentPair] = []
    for document_number in sorted(metadata.keys() & texts.keys()):
        meta = metadata[document_number]
        sha, text = texts[document_number]
        pairs.append(
            DocumentPair(
                document_number=document_number,
                title=str(meta.get("title", "")),
                url=str(meta.get("html_url", "")),
                text_sha256=sha,
                text=text,
            )
        )
    return pairs


def extract_obligations(
    provider: LLMProvider, text: str, *, workers: int = 1
) -> list[ExtractedObligation]:
    """Run the model over paragraph-aligned chunks and concatenate its proposals.

    Chunks may be extracted concurrently (``workers`` > 1) but their results are
    always reassembled in chunk order, so the output does not depend on
    scheduling. Verified bit-identical to a serial run at temperature 0 with a
    pinned seed.

    Failure mode: a chunk whose model response is invalid or errors out yields
    NO obligations (fail-closed — logged, never guessed at); other chunks
    still process, so one bad response cannot sink a document.
    """
    logger = structlog.get_logger()
    chunks = list(chunk_text(text))

    def extract_chunk(indexed: tuple[int, str]) -> list[ExtractedObligation]:
        index, chunk = indexed
        try:
            return provider.extract(chunk).obligations
        except (ValidationError, httpx.HTTPError) as error:
            # Fail-closed: an unparseable or failed chunk contributes nothing.
            logger.warning("chunk-extraction-failed", chunk_index=index, error=type(error).__name__)
            return []

    if workers <= 1:
        per_chunk = [extract_chunk(item) for item in enumerate(chunks)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # pool.map preserves input order, so the concatenation stays deterministic.
            per_chunk = list(pool.map(extract_chunk, enumerate(chunks)))
    return [obligation for group in per_chunk for obligation in group]


def _bounded_text(text: str, max_chars: int) -> str:
    """Cap very long documents at a paragraph boundary; coverage is recorded, not hidden."""
    if len(text) <= max_chars:
        return text
    cut = text.rfind("\n\n", 0, max_chars)
    return text[: cut if cut > 0 else max_chars]


def document_run_meta(provider: LLMProvider, pair: DocumentPair, max_chars: int) -> RunMeta:
    """The determinism record a run of ``pair`` would produce, without calling the model.

    Shared by :func:`gate_document` and the reuse check so the two can never
    disagree about what identifies a run.
    """
    return provider.run_meta(input_sha256(_bounded_text(pair.text, max_chars)))


def gate_document(
    provider: LLMProvider, pair: DocumentPair, max_chars: int = 80_000, *, workers: int = 1
) -> DocumentExtraction:
    """Extract one document (bounded) and pass every claim through the provenance gate."""
    extraction_text = _bounded_text(pair.text, max_chars)
    run_meta = document_run_meta(provider, pair, max_chars)
    claims: list[ClaimRecord] = []
    seen: set[str] = set()
    for obligation in extract_obligations(provider, extraction_text, workers=workers):
        identifier = claim_id(pair.text_sha256, obligation)
        if identifier in seen:
            continue  # identical span re-proposed by another chunk
        seen.add(identifier)
        verdict = verify_span(pair.text, obligation.quote)
        claims.append(
            ClaimRecord(
                claim_id=identifier,
                document_sha256=pair.text_sha256,
                document_number=pair.document_number,
                document_title=pair.title,
                document_url=pair.url,
                quote=obligation.quote,
                obligation_type=str(obligation.obligation_type),
                affected_party=obligation.affected_party,
                summary=obligation.summary,
                effective_date=obligation.effective_date,
                accepted=verdict.accepted,
                start=verdict.start,
                end=verdict.end,
                rejection_reason=verdict.reason,
                run=run_meta,
            )
        )
    accepted = sum(1 for claim in claims if claim.accepted)
    return DocumentExtraction(
        document_sha256=pair.text_sha256,
        document_number=pair.document_number,
        document_title=pair.title,
        document_url=pair.url,
        accepted_count=accepted,
        rejected_count=len(claims) - accepted,
        total_chars=len(pair.text),
        extracted_chars=len(extraction_text),
        claims=claims,
    )


def _persist(processed_dir: Path, extractions: list[DocumentExtraction]) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    payload = [extraction.model_dump() for extraction in extractions]
    (processed_dir / "claims.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_persisted(processed_dir: Path) -> dict[str, DocumentExtraction]:
    """Previously extracted documents, keyed by source-text SHA-256.

    Failure mode: a missing or unparseable claims.json yields an empty mapping,
    so a corrupt checkpoint costs re-extraction rather than wrong results.
    """
    claims_path = processed_dir / "claims.json"
    if not claims_path.is_file():
        return {}
    try:
        payload = json.loads(claims_path.read_text())
        extractions = [DocumentExtraction.model_validate(item) for item in payload]
    except (json.JSONDecodeError, ValidationError):
        return {}
    return {extraction.document_sha256: extraction for extraction in extractions}


def reusable_extraction(
    persisted: dict[str, DocumentExtraction], pair: DocumentPair, expected_run: RunMeta
) -> DocumentExtraction | None:
    """A prior extraction of ``pair`` iff it is provably the same run, else None.

    Reuse requires the source SHA to match and EVERY persisted claim to carry an
    identical run record (model tag, prompt hash, input hash, temperature), so a
    changed model or prompt invalidates the cache automatically. Failure mode: a
    document with no persisted claims is never reused — an empty result carries
    no run record, so its provenance cannot be established and it is re-extracted
    (fail-closed).
    """
    previous = persisted.get(pair.text_sha256)
    if previous is None or not previous.claims:
        return None
    if any(claim.run != expected_run for claim in previous.claims):
        return None
    return previous


def run_pipeline(
    settings: Settings, provider: LLMProvider, *, force: bool = False
) -> list[DocumentExtraction]:
    """Extract + gate every discovered document; persist to data/processed/claims.json.

    Idempotent: a document whose source SHA, model tag and prompt hash already
    appear in claims.json is reused rather than re-inferred, so re-running over
    an unchanged corpus is a no-op and an interrupted run resumes where it
    stopped. ``force=True`` re-extracts everything. Checkpoints after every
    document so a long run interrupted midway still leaves a valid,
    self-consistent claims.json on disk.
    """
    logger = structlog.get_logger()
    processed_dir = settings.data_dir / "processed"
    persisted = {} if force else load_persisted(processed_dir)
    extractions: list[DocumentExtraction] = []
    for pair in discover_documents(settings.data_dir):
        expected_run = document_run_meta(provider, pair, settings.max_document_chars)
        cached = reusable_extraction(persisted, pair, expected_run)
        if cached is not None:
            extractions.append(cached)
            logger.info("document-reused", document=pair.document_number)
            continue
        extraction = gate_document(
            provider,
            pair,
            max_chars=settings.max_document_chars,
            workers=settings.extract_workers,
        )
        extractions.append(extraction)
        _persist(processed_dir, extractions)
        logger.info(
            "document-extracted",
            document=pair.document_number,
            accepted=extraction.accepted_count,
            rejected=extraction.rejected_count,
        )
    _persist(processed_dir, extractions)
    return extractions
