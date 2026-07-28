"""Extraction pipeline: snapshots -> chunks -> LLM -> provenance gate -> records.

Inputs: content-addressed snapshots under ``data/raw/``. Outputs: a list of
:class:`DocumentExtraction` (accepted AND rejected claims — rejections are
counted, never hidden). Failure mode: a document with no metadata/text pair is
skipped with nothing recorded; a claim that cannot be verified is recorded as
rejected (fail-closed, see ``reglens.provenance``).
"""

import json
from pathlib import Path
from typing import NamedTuple

import httpx
import structlog
from pydantic import ValidationError

from reglens.config import Settings
from reglens.extract.chunk import chunk_text
from reglens.extract.llm import LLMProvider, input_sha256
from reglens.extract.records import ClaimRecord, DocumentExtraction, claim_id
from reglens.extract.schema import ExtractedObligation
from reglens.ingest.snapshot import read_manifest
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
    raw_root = data_dir / "raw"
    if not raw_root.is_dir():
        return []
    metadata: dict[str, dict[str, str]] = {}
    texts: dict[str, tuple[str, str]] = {}
    for snapshot_dir in sorted(raw_root.iterdir()):
        manifest_path = snapshot_dir / "manifest.json"
        if not manifest_path.is_file():
            continue  # incomplete snapshot: ignored, never guessed at
        manifest = read_manifest(snapshot_dir)
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


def extract_obligations(provider: LLMProvider, text: str) -> list[ExtractedObligation]:
    """Run the model over paragraph-aligned chunks and concatenate its proposals.

    Failure mode: a chunk whose model response is invalid or errors out yields
    NO obligations (fail-closed — logged, never guessed at); other chunks
    still process, so one bad response cannot sink a document.
    """
    logger = structlog.get_logger()
    obligations: list[ExtractedObligation] = []
    for index, chunk in enumerate(chunk_text(text)):
        try:
            obligations.extend(provider.extract(chunk).obligations)
        except (ValidationError, httpx.HTTPError) as error:
            # Fail-closed: an unparseable or failed chunk contributes nothing.
            logger.warning("chunk-extraction-failed", chunk_index=index, error=type(error).__name__)
    return obligations


def _bounded_text(text: str, max_chars: int) -> str:
    """Cap very long documents at a paragraph boundary; coverage is recorded, not hidden."""
    if len(text) <= max_chars:
        return text
    cut = text.rfind("\n\n", 0, max_chars)
    return text[: cut if cut > 0 else max_chars]


def gate_document(
    provider: LLMProvider, pair: DocumentPair, max_chars: int = 80_000
) -> DocumentExtraction:
    """Extract one document (bounded) and pass every claim through the provenance gate."""
    extraction_text = _bounded_text(pair.text, max_chars)
    run_meta = provider.run_meta(input_sha256(extraction_text))
    claims: list[ClaimRecord] = []
    seen: set[str] = set()
    for obligation in extract_obligations(provider, extraction_text):
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


def run_pipeline(settings: Settings, provider: LLMProvider) -> list[DocumentExtraction]:
    """Extract + gate every discovered document; persist to data/processed/claims.json.

    Checkpoints after every document so a long run interrupted midway still
    leaves a valid, self-consistent claims.json on disk.
    """
    logger = structlog.get_logger()
    processed_dir = settings.data_dir / "processed"
    extractions: list[DocumentExtraction] = []
    for pair in discover_documents(settings.data_dir):
        extraction = gate_document(provider, pair, max_chars=settings.max_document_chars)
        extractions.append(extraction)
        _persist(processed_dir, extractions)
        logger.info(
            "document-extracted",
            document=pair.document_number,
            accepted=extraction.accepted_count,
            rejected=extraction.rejected_count,
        )
    return extractions
