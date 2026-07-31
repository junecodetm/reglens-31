"""Persisted claim records — every claim carries its gate verdict and run provenance."""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from reglens.extract.schema import ExtractedObligation, RunMeta


class ClaimRecord(BaseModel):
    """One extracted obligation after the provenance gate has ruled on it."""

    claim_id: str
    document_sha256: str
    document_number: str
    document_title: str
    document_url: str
    quote: str
    obligation_type: str
    affected_party: str
    summary: str
    effective_date: str | None
    accepted: bool
    start: int | None
    end: int | None
    rejection_reason: str | None
    run: RunMeta


class DocumentExtraction(BaseModel):
    """All claims for one source document, accepted and rejected alike."""

    document_sha256: str
    document_number: str
    document_title: str
    document_url: str
    accepted_count: int
    rejected_count: int
    total_chars: int
    extracted_chars: int
    run: RunMeta | None = None
    """The run that produced this document, whether or not it yielded any claims.

    Recorded at the document level because provenance is a property of the run,
    not of its output: a document the model read and found nothing in has a real,
    checkable run record, and without this field it was indistinguishable from a
    document never processed at all — so it was re-inferred on every pass and the
    idempotency guarantee quietly did not hold for it. ``None`` marks a record
    written before this field existed; it never matches a computed run, so such a
    document is re-extracted rather than trusted (fail-closed).
    """
    claims: list[ClaimRecord]


def load_extractions(claims_path: Path) -> list[DocumentExtraction]:
    """Validated read of claims.json — the ONLY sanctioned way to consume it.

    Failure mode: pydantic ``ValidationError`` on malformed records; downstream
    consumers never operate on unvalidated dicts (docs/STANDARDS.md).
    """
    return [DocumentExtraction.model_validate(item) for item in json.loads(claims_path.read_text())]


def claim_id(document_sha256: str, obligation: ExtractedObligation) -> str:
    """Deterministic id: same document + same claimed span → same id across runs."""
    digest = hashlib.sha256(
        f"{document_sha256}\x00{obligation.quote}\x00{obligation.obligation_type}".encode()
    )
    return digest.hexdigest()[:16]
