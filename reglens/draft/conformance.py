"""Structural conformance checker + fabrication/quote gates for drafts.

Inputs: one generated skeleton, the model-generated narrative fields, and
the verification corpus (part text, authority line, cited U.S.C. section
texts). Outputs: a per-draft checklist; a draft failing ANY check is
REJECTED — never published with a caveat. Failure mode: fail-closed
throughout; a check that cannot run counts as failed.

The checklist measures verifiable structure. Substantive accuracy remains a
matter for human review.
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
# Any hit rejects the whole draft because a skeleton that invents a cost
# estimate, docket, RIN, date, or contact is defective.
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
_AMENDATORY_FORMS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Amend § \d+\.___ by adding paragraph"),
    re.compile(r"Revise § \d+\.___ to read as follows:"),
    re.compile(r"Remove and reserve § \d+\.___"),
)


class DraftDossier(BaseModel):
    """Replay metadata for one narrative generation.

    Inputs are the actual model settings, model-bound prompt digests, and the
    part snapshot digest. ``prompt_sha256``/``system_prompt_sha256`` cover the
    exact bytes the model received; ``input_sha256`` is the source CFR part
    snapshot of record, which is NOT itself sent to the model (the prompt
    carries only part number, heading, authority line, and doc type) — the UI
    labels it accordingly. Provider-specific knobs are recorded only where
    they apply: the local runtime records ``num_ctx``/``num_predict``, the
    hosted provider records ``max_tokens``/``reasoning_effort``; the unused
    pair is ``None``. Output is a JSON-safe dossier; invalid or missing
    fields raise through Pydantic, so provenance cannot silently degrade.
    """

    provider: str = "local"
    model: str
    temperature: float
    seed: int
    num_ctx: int | None
    num_predict: int | None
    max_tokens: int | None = None
    reasoning_effort: str | None = None
    system_prompt_sha256: str
    prompt_sha256: str
    input_sha256: str
    narrative_fields: list[str]


class DraftChecklist(BaseModel):
    """Structural conformance results for one draft (all must hold to pass)."""

    part: int
    doc_type: str
    headings_in_order: bool
    analysis_sections_present: bool
    placeholders_intact: bool
    amendatory_instructions_parse: bool
    amendatory_forms_demonstrated: bool
    authority_citation_present: bool
    basis_and_purpose_present: bool
    comment_period_reference: bool
    setout_text_verified: bool
    narrative_fabrication_clean: bool
    quotes_verified: bool
    unverified_quote_count: int
    fabrication_hits: list[str] = Field(default_factory=list[str])
    dossier: DraftDossier
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


def _amendatory_forms_demonstrated(draft: str) -> bool:
    marker = draft.find("Amendatory Instructions")
    if marker < 0:
        return False
    numbered = "\n".join(
        match.group(0) for match in re.finditer(r"^\d+\..*$", draft[marker:], re.MULTILINE)
    )
    return all(pattern.search(numbered) is not None for pattern in _AMENDATORY_FORMS)


def _authority_citation_present(part: int, draft: str) -> bool:
    marker = f"The authority citation for part {part} continues to read as follows:"
    line = re.search(rf"^\d+\.\s+{re.escape(marker)}[ \t]*$", draft, re.MULTILINE)
    if line is None:
        return False
    tail = draft[line.end() :]
    next_instruction = re.search(r"^\d+\.\s", tail, re.MULTILINE)
    block = tail[: next_instruction.start()] if next_instruction is not None else tail
    return bool(block.strip())


def _basis_and_purpose_present(draft: str) -> bool:
    return all(
        marker in draft for marker in ("SUMMARY:", "SUPPLEMENTARY INFORMATION:", "I. Background")
    )


def _comment_period_reference(doc_type: str, draft: str) -> bool:
    if doc_type == "nprm":
        return "Comments must be received on or before" in draft
    if doc_type == "final":
        return "Effective date:" in draft
    return False  # fail-closed: an unknown draft type has no valid timing caption


_INSTRUCTION_LINE = re.compile(r"^\d+\.\s", re.MULTILINE)


def _setout_text_verified(draft: str, corpus: list[str]) -> bool:
    """EVERY paragraph set out after "read as follows:" must gate-verify or be
    a placeholder. The region runs to the next numbered instruction (or end of
    draft), so a fabricated second paragraph or extra blank line cannot slip
    past a first-paragraph-only window; an empty set-out region is itself a
    defect. Fail-closed throughout."""
    for match in re.finditer(r"read as follows:", draft):
        next_instruction = _INSTRUCTION_LINE.search(draft, match.end())
        region_end = next_instruction.start() if next_instruction else len(draft)
        paragraphs = [
            stripped
            for paragraph in draft[match.end() : region_end].split("\n\n")
            if (stripped := paragraph.strip())
        ]
        if not paragraphs:
            return False  # fail-closed: an empty set-out region is a defect
        for paragraph in paragraphs:
            if paragraph == PLACEHOLDER:
                continue
            if not any(verify_span(source, paragraph).accepted for source in corpus):
                return False  # fail-closed: unverifiable set-out text
    return True


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
    *,
    dossier: DraftDossier,
) -> DraftChecklist:
    """Run every gate and attach the generation dossier.

    Inputs are one draft, its narrative/corpus, and required provenance;
    output is a typed checklist. Each unverifiable path records ``False`` and
    ``passed`` requires every structural and fabrication check to hold.
    """
    fabrication = scan_fabrication(narrative)
    unverified_quotes = verify_narrative_quotes(narrative, corpus)
    checklist = DraftChecklist(
        part=part,
        doc_type=doc_type,
        headings_in_order=_headings_in_order(draft),
        analysis_sections_present=_analysis_sections_present(draft),
        placeholders_intact=_placeholders_intact(draft),
        amendatory_instructions_parse=_amendatory_instructions_parse(draft),
        amendatory_forms_demonstrated=_amendatory_forms_demonstrated(draft),
        authority_citation_present=_authority_citation_present(part, draft),
        basis_and_purpose_present=_basis_and_purpose_present(draft),
        comment_period_reference=_comment_period_reference(doc_type, draft),
        setout_text_verified=_setout_text_verified(draft, corpus),
        narrative_fabrication_clean=not fabrication,
        quotes_verified=unverified_quotes == 0,
        unverified_quote_count=unverified_quotes,
        fabrication_hits=fabrication,
        dossier=dossier,
        passed=False,
    )
    checklist.passed = all(
        (
            checklist.headings_in_order,
            checklist.analysis_sections_present,
            checklist.placeholders_intact,
            checklist.amendatory_instructions_parse,
            checklist.amendatory_forms_demonstrated,
            checklist.authority_citation_present,
            checklist.basis_and_purpose_present,
            checklist.comment_period_reference,
            checklist.setout_text_verified,
            checklist.narrative_fabrication_clean,
            checklist.quotes_verified,
        )
    )
    return checklist
