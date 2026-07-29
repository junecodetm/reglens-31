"""Two-sided textual-marker retrieval over Federal Register document text.

Inputs: the full text of one FR document (preamble + regulatory text as
published). Outputs: exact, gate-verified marker spans in TWO families of
equal weight — deference-reliance AND grounding-strength — plus per-document
facts. Failure mode: a span that fails the provenance gate is counted as a
rejection and excluded (fail-closed; expected zero by construction since the
patterns match the same text they quote — reported as a guardrail).

This is a retrieval task, never a prediction task (EXTEND-OGC01 §0.2). No
marker, count, density, or band states or implies anything about a
regulation's validity or any judicial outcome. The analytic *West Virginia
v. EPA* marker ("reliance on general authority to reach a major question")
is NOT literally searchable and is therefore out of scope — a limitation
stated in docs/OGC01-ALIGNMENT.md.
"""

import re

from pydantic import BaseModel, Field

from reglens.provenance import verify_span

GROUNDING_SCHEMA_VERSION = 1

LOPER_BRIGHT_DECIDED = "2024-06-28"

# (family key, side, compiled pattern). Literal phrase families only —
# documented here, in the UI copy, and in docs/OGC01-ALIGNMENT.md.
# "Chevron" stays case-sensitive: it is a proper-noun case citation.
_DEFERENCE = "deference-reliance"
_GROUNDING = "grounding-strength"

MARKER_FAMILIES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("chevron-citation", _DEFERENCE, re.compile(r"\bChevron\b")),
    ("silent-or-ambiguous", _DEFERENCE, re.compile(r"\bsilent\s+or\s+ambiguous\b", re.I)),
    (
        "permissible-construction",
        _DEFERENCE,
        re.compile(r"\bpermissible\s+construction\b", re.I),
    ),
    (
        "reasonable-interpretation",
        _DEFERENCE,
        re.compile(r"\breasonable\s+interpretation\b", re.I),
    ),
    ("major-questions", _DEFERENCE, re.compile(r"\bmajor\s+questions?\b", re.I)),
    (
        "necessary-and-appropriate",
        _DEFERENCE,
        re.compile(r"\bnecessary\s+and\s+appropriate\b", re.I),
    ),
    (
        "directs-the-secretary",
        _GROUNDING,
        re.compile(r"\b(?:directs?|directed)\s+the\s+Secretary\b", re.I),
    ),
    (
        "requires-the-secretary",
        _GROUNDING,
        re.compile(r"\brequires?\s+the\s+Secretary\b", re.I),
    ),
    ("as-required-by", _GROUNDING, re.compile(r"\bas\s+required\s+by\b", re.I)),
    (
        "statutory-definition",
        _GROUNDING,
        re.compile(r"\b(?:the\s+statute\s+defines|statutory\s+definition)\b", re.I),
    ),
    (
        "express-delegation",
        _GROUNDING,
        re.compile(r"\bexpress(?:ly)?\s+(?:delegat\w+|authoriz\w+|requir\w+|direct\w+)\b", re.I),
    ),
    (
        "congressional-direction",
        _GROUNDING,
        re.compile(
            r"\b(?:Congress\s+(?:directed|has\s+directed|ratified)|statutory\s+mandate)\b",
            re.I,
        ),
    ),
)

# Density bands are TEXTUAL-MARKER DENSITY only (markers per 1,000 words),
# applied identically to both families. They describe how often the listed
# phrases appear — nothing else. Thresholds are definitional, not empirical:
# none = 0 markers; low ≤ 0.2/1k words; moderate ≤ 0.6/1k; elevated > 0.6/1k.
DENSITY_LOW_MAX = 0.2
DENSITY_MODERATE_MAX = 0.6


class MarkerSpan(BaseModel):
    """One exact marker occurrence, gate-verified against the source text."""

    family: str = Field(max_length=60)
    side: str = Field(max_length=30)
    quote: str = Field(max_length=300)
    start: int
    end: int


class MarkerScan(BaseModel):
    """All markers found in one document, plus the gate guardrail count."""

    schema_version: int = GROUNDING_SCHEMA_VERSION
    markers: list[MarkerSpan]
    gate_rejections: int
    word_count: int


def density_band(count: int, word_count: int) -> tuple[float, str]:
    """(markers per 1,000 words, band label) — purely definitional."""
    if word_count <= 0 or count == 0:
        return 0.0, "none"
    density = count * 1000.0 / word_count
    if density <= DENSITY_LOW_MAX:
        return density, "low"
    if density <= DENSITY_MODERATE_MAX:
        return density, "moderate"
    return density, "elevated"


def scan_markers(text: str) -> MarkerScan:
    """Find every marker span in ``text``; verify each through the gate."""
    markers: list[MarkerSpan] = []
    rejections = 0
    for family, side, pattern in MARKER_FAMILIES:
        for match in pattern.finditer(text):
            gate = verify_span(text, match.group(0))
            if not gate.accepted or gate.start is None or gate.end is None:
                # Fail-closed guardrail: a marker that cannot be re-verified
                # verbatim is counted as rejected and never reported as found.
                rejections += 1
                continue
            markers.append(
                MarkerSpan(
                    family=family,
                    side=side,
                    quote=match.group(0),
                    start=match.start(),
                    end=match.end(),
                )
            )
    markers.sort(key=lambda span: (span.start, span.end))
    return MarkerScan(
        markers=markers,
        gate_rejections=rejections,
        word_count=len(text.split()),
    )
