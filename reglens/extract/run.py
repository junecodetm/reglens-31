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
    """Run the model over paragraph-aligned chunks and concatenate its proposals."""
    obligations: list[ExtractedObligation] = []
    for chunk in chunk_text(text):
        obligations.extend(provider.extract(chunk).obligations)
    return obligations


def gate_document(provider: LLMProvider, pair: DocumentPair) -> DocumentExtraction:
    """Extract one document and pass every claim through the provenance gate."""
    run_meta = provider.run_meta(input_sha256(pair.text))
    claims: list[ClaimRecord] = []
    seen: set[str] = set()
    for obligation in extract_obligations(provider, pair.text):
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
        claims=claims,
    )


def run_pipeline(settings: Settings, provider: LLMProvider) -> list[DocumentExtraction]:
    """Extract + gate every discovered document; persist to data/processed/claims.json."""
    extractions = [gate_document(provider, pair) for pair in discover_documents(settings.data_dir)]
    processed_dir = settings.data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    payload = [extraction.model_dump() for extraction in extractions]
    (processed_dir / "claims.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return extractions
