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
