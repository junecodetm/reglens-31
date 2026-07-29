"""Structural conformance checker + fabrication/quote gates for drafts.

Inputs: one generated skeleton, the model-generated narrative fields, and
the verification corpus (part text, authority line, cited U.S.C. section
texts). Outputs: a per-draft checklist; a draft failing ANY check is
REJECTED — never published with a caveat (EXTEND-OGC01 Stage 3.4). Failure
mode: fail-closed throughout; a check that cannot run counts as failed.

This checklist is the only honest "accuracy" metric available for
generation (Stage 3.5): structure is verifiable; substance is the human's.
"""

import re

from pydantic import BaseModel, Field

from reglens.draft.templates import ANALYSIS_SECTIONS, PLACEHOLDER, PREAMBLE_CAPTIONS
from reglens.provenance import verify_span

# Pre-normalization applied ONLY inside this checker before quote detection/
# verification: curly quotes fold to straight quotes. This extends — without
# modifying — the core provenance normalization, and is documented here and
# in docs/OGC01-ALIGNMENT.md. NFKC does not fold these characters.
# U+2018/U+2019/U+201C/U+201D = curly single/double quotes, written escaped
# so the fold table is unambiguous to linters and readers.
_QUOTE_FOLD = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})

# Both double- AND single-quoted spans are gate-checked (curly quotes fold
# to straight first). The floor keeps apostrophes/contractions out of the
# matcher; the narrative SYSTEM prompt bans quotation entirely, so any
# quote-looking span at all is already suspect.
_QUOTED_STRING = re.compile(r"\"([^\"]{15,})\"|'([^']{15,})'")
MIN_QUOTE_CHARS = 15

# Fabrication scan over MODEL-GENERATED narrative only: the deterministic
# template contains no such content by construction (asserted in tests).
# Any hit rejects the whole draft — a skeleton that silently invents a cost
# estimate, docket, RIN, date, or contact is a defect (Stage 3.3).
_FABRICATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rin", re.compile(r"\bRIN\s*\d{4}-[A-Z]{2}\d{2}\b")),
    ("docket-id", re.compile(r"\b[A-Z]{2,10}-\d{4}-\d{3,}\b")),
    ("dollar-amount", re.compile(r"\$\s?\d")),
    ("phone", re.compile(r"(?:\(\d{3}\)\s?|\b\d{3}[-.])\d{3}[-.]\d{4}\b")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")),
    (
        "calendar-date",
        re.compile(
            r"\b(?:January|February|March|April|May|June|July|August|September|"
            r"October|November|December)\s+\d{1,2},\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b"
        ),
    ),
    # An injected URL must never ride a narrative into a published draft.
    ("url", re.compile(r"https?://|\bwww\.[\w-]+\.\w{2,}", re.IGNORECASE)),
)

_AMENDATORY_LINE = re.compile(r"^\d+\.\s+\S", re.MULTILINE)
_AMENDATORY_OK = re.compile(
    r"^\d+\.\s+(?:The authority citation for part \d+ continues to read as follows:"
    r"|\[PLACEHOLDER|Amend\b|Revise\b|Add\b|Remove\b)"
)


class DraftChecklist(BaseModel):
    """Structural conformance results for one draft (all must hold to pass)."""

    part: int
    doc_type: str
    headings_in_order: bool
    analysis_sections_present: bool
    placeholders_intact: bool
    amendatory_instructions_parse: bool
    setout_text_verified: bool
    narrative_fabrication_clean: bool
    quotes_verified: bool
    unverified_quote_count: int
    fabrication_hits: list[str] = Field(default_factory=list[str])
    passed: bool


def _headings_in_order(draft: str) -> bool:
    positions = [draft.find(caption) for caption in PREAMBLE_CAPTIONS]
    return all(p >= 0 for p in positions) and positions == sorted(positions)


def _analysis_sections_present(draft: str) -> bool:
    return all(name in draft for name in ANALYSIS_SECTIONS)


def _placeholders_intact(draft: str) -> bool:
    """Every analysis section must still contain a visible placeholder.

    The window for each section runs to the NEXT section heading (or the
    List of Subjects), so a neighboring section's placeholder can never
    satisfy a silently filled stub. Fail-closed on any missing section.
    """
    boundaries = [*ANALYSIS_SECTIONS, "List of Subjects"]
    for position, name in enumerate(ANALYSIS_SECTIONS):
        index = draft.find(name)
        if index < 0:
            return False
        next_index = draft.find(boundaries[position + 1], index + len(name))
        window = draft[index : next_index if next_index > index else len(draft)]
        if PLACEHOLDER not in window:
            return False  # fail-closed: a silently filled stub is a defect
    return True


def _amendatory_instructions_parse(draft: str) -> bool:
    lines = _AMENDATORY_LINE.findall(draft)
    if not lines:
        return False
    marker = draft.find("Amendatory Instructions")
    if marker < 0:
        return False
    tail = draft[marker:]
    numbered = [m.group(0) for m in re.finditer(r"^\d+\..*$", tail, re.MULTILINE)]
    return bool(numbered) and all(_AMENDATORY_OK.match(line) for line in numbered)


def _setout_text_verified(draft: str, corpus: list[str]) -> bool:
    """Text set out after "read as follows:" must gate-verify or be a placeholder."""
    verified = True
    for match in re.finditer(r"read as follows:\n\n?(.*?)(?:\n\n|\Z)", draft, re.DOTALL):
        block = match.group(1).strip()
        if not block or PLACEHOLDER in block:
            continue
        if not any(verify_span(source, block).accepted for source in corpus):
            verified = False  # fail-closed: unverifiable set-out text
    return verified


def scan_fabrication(narrative: str) -> list[str]:
    """Names of fabrication patterns found in the model narrative."""
    folded = narrative.translate(_QUOTE_FOLD)
    return [name for name, pattern in _FABRICATION_PATTERNS if pattern.search(folded)]


def verify_narrative_quotes(narrative: str, corpus: list[str]) -> int:
    """Count quoted strings (≥15 chars) that fail the gate against every source."""
    folded = narrative.translate(_QUOTE_FOLD)
    unverified = 0
    for match in _QUOTED_STRING.finditer(folded):
        quote = match.group(1) or match.group(2)
        if not any(verify_span(source, quote).accepted for source in corpus):
            unverified += 1  # fail-closed: an unverifiable quote rejects the draft
    return unverified


def check_draft(
    part: int,
    doc_type: str,
    draft: str,
    narrative: str,
    corpus: list[str],
) -> DraftChecklist:
    """Run the full checklist; ``passed`` requires every check to hold."""
    fabrication = scan_fabrication(narrative)
    unverified_quotes = verify_narrative_quotes(narrative, corpus)
    checklist = DraftChecklist(
        part=part,
        doc_type=doc_type,
        headings_in_order=_headings_in_order(draft),
        analysis_sections_present=_analysis_sections_present(draft),
        placeholders_intact=_placeholders_intact(draft),
        amendatory_instructions_parse=_amendatory_instructions_parse(draft),
        setout_text_verified=_setout_text_verified(draft, corpus),
        narrative_fabrication_clean=not fabrication,
        quotes_verified=unverified_quotes == 0,
        unverified_quote_count=unverified_quotes,
        fabrication_hits=fabrication,
        passed=False,
    )
    checklist.passed = all(
        (
            checklist.headings_in_order,
            checklist.analysis_sections_present,
            checklist.placeholders_intact,
            checklist.amendatory_instructions_parse,
            checklist.setout_text_verified,
            checklist.narrative_fabrication_clean,
            checklist.quotes_verified,
        )
    )
    return checklist
