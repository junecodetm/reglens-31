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

    quote: str = Field(
        max_length=4000, description="Verbatim span copied exactly from the source text"
    )
    obligation_type: ObligationType
    affected_party: str = Field(
        max_length=300, description="Who must comply, as named in the source"
    )
    summary: str = Field(max_length=500, description="One-sentence restatement of the obligation")
    effective_date: str | None = Field(
        default=None,
        max_length=100,
        description="Effective/compliance date if stated in the source, else null",
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
    runtime: str = "unknown"
    """Inference runtime and version, e.g. ``ollama/0.30.7``.

    The runtime is a real input to the output: an upgrade silently changed
    structured-output behaviour once already, and a determinism record that
    names only the model cannot distinguish that from a model change.
    """
    chunk_plan_sha256: str = "unknown"
    """Identity of the chunk sequence the model was shown (``chunk.chunk_plan_sha256``).

    The model reads one chunk at a time, so where the boundaries fall is a real
    input to the output. Without this field a change to the chunker leaves the
    reuse key unchanged and stale results are silently kept — which is exactly
    what happened when paragraph-only splitting was replaced. ``"unknown"``
    marks a record produced before the field existed; it is never backfilled,
    and it can never match a computed plan, so such a document is re-extracted
    rather than trusted (fail-closed).
    """


def prompt_sha256(system_prompt: str, user_template: str) -> str:
    """Stable hash identifying the exact prompt pair used for a run."""
    return hashlib.sha256((system_prompt + "\x00" + user_template).encode()).hexdigest()
