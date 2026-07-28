"""Pydantic contracts for extraction.

Inputs: raw model JSON. Outputs: validated records. Failure mode: pydantic
``ValidationError`` — a malformed model response is rejected, never coerced.
"""

import hashlib
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

EXTRACTION_SCHEMA_VERSION = 1


class ObligationType(StrEnum):
    REQUIREMENT = "requirement"
    PROHIBITION = "prohibition"
    REPORTING = "reporting"
    RECORDKEEPING = "recordkeeping"
    DISCLOSURE = "disclosure"
    OTHER = "other"


class ExtractedObligation(BaseModel):
    """One obligation as proposed by the model — unverified until the provenance gate runs."""

    model_config = ConfigDict(extra="forbid")

    quote: str = Field(description="Verbatim span copied exactly from the source text")
    obligation_type: ObligationType
    affected_party: str = Field(description="Who must comply, as named in the source")
    summary: str = Field(description="One-sentence restatement of the obligation")
    effective_date: str | None = Field(
        default=None, description="Effective/compliance date if stated in the source, else null"
    )


class ExtractionResult(BaseModel):
    """The model's full response for one chunk of source text."""

    model_config = ConfigDict(extra="forbid")

    obligations: list[ExtractedObligation]


class RunMeta(BaseModel):
    """Determinism record for one extraction run (docs/STANDARDS.md)."""

    schema_version: int = EXTRACTION_SCHEMA_VERSION
    model_tag: str
    prompt_sha256: str
    input_sha256: str
    temperature: float = 0.0


def prompt_sha256(system_prompt: str, user_template: str) -> str:
    """Stable hash identifying the exact prompt pair used for a run."""
    return hashlib.sha256((system_prompt + "\x00" + user_template).encode()).hexdigest()
