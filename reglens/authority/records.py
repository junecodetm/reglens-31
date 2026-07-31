"""Typed records for the statutory authority linker.

Inputs: parsed authority citations and resolved U.S.C. section texts.
Outputs: the pydantic models persisted to ``data/processed/authority.json``
and exported to the static site. Failure mode: pydantic ``ValidationError``
on malformed values; no untyped dicts cross module boundaries.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

AUTHORITY_SCHEMA_VERSION = 1


class CitationKind(StrEnum):
    """How a single authority citation resolves.

    Only ``usc_section`` enters verb-phrase classification. Note, public-law,
    and executive-order citations are *coverage categories* — they resolve to
    material outside codified USLM section text and must never be quoted as if
    they were the codified section (e.g. "15 U.S.C. 6701 note" is TRIA, not
    the codified §6701).
    """

    usc_section = "usc-section"
    usc_note = "usc-note"
    public_law = "public-law"
    executive_order = "executive-order"


class Classification(StrEnum):
    """Operative-grant classification of one resolved U.S.C. section."""

    mandatory = "mandatory"
    discretionary = "discretionary"
    silent = "silent"
    unresolved = "unresolved"


class AuthorityCitation(BaseModel):
    """One citation parsed from a part's authority line."""

    raw: str = Field(max_length=500)
    kind: CitationKind
    usc_title: int | None = None
    usc_section: str | None = None
    subsection: str | None = None
    et_seq: bool = False
    from_range: str | None = None


class GrantSpan(BaseModel):
    """One matched operative verb phrase inside a section's text."""

    family: str = Field(max_length=60)
    classification: Classification
    quote: str = Field(max_length=500)
    start: int
    end: int


class ResolvedSection(BaseModel):
    """A ``usc_section`` citation resolved against pinned USLM XML."""

    usc_title: int
    usc_section: str
    identifier: str
    heading: str | None = None
    status: str | None = None
    text_sha256: str
    classification: Classification
    # The winning verb phrase, present only when classification is
    # mandatory/discretionary AND the quote passed the provenance gate.
    verb_quote: str | None = None
    verb_start: int | None = None
    verb_end: int | None = None
    grant_spans: list[GrantSpan] = Field(default_factory=list[GrantSpan])
    gate_rejected: bool = False
    rejection_reason: str | None = None


class PartAuthority(BaseModel):
    """Everything the UI and eval need for one CFR part's authority citation."""

    schema_version: int = AUTHORITY_SCHEMA_VERSION
    cfr_title: int = 31
    part: int
    part_heading: str
    ecfr_date: str
    authority_text: str
    # Offsets of the authority citation inside the part's flattened text
    # snapshot (for click-to-highlight), gate-verified at build.
    part_text_sha256: str
    authority_start: int
    authority_end: int
    citations: list[AuthorityCitation]
    resolved: list[ResolvedSection]
    # usc_section cites that could not be found in the pinned USLM release —
    # Fail-closed: recorded, never guessed at.
    unresolved: list[AuthorityCitation]
    ecfr_url: str


class AuthorityExport(BaseModel):
    """Top-level payload for ``authority.json``."""

    schema_version: int = AUTHORITY_SCHEMA_VERSION
    usc_release_point: str
    generated_from: str
    parts: list[PartAuthority]
    total_section_citations: int
    total_resolved: int
    total_unresolved: int
    total_non_section_citations: int
    gate_rejections: int
