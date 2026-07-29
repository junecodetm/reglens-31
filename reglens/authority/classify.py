"""Deterministic operative-grant classification of U.S.C. section text.

Inputs: the flattened text of one resolved U.S.C. section. Outputs: a
classification in {mandatory, discretionary, silent} plus every matched
grant span. Failure mode: none of the patterns matching yields ``silent``
(a documented outcome, not an error); pattern quotes are later gate-verified
by the caller and rejected fail-closed if verification fails.

This is retrieval, not inference: no LLM is involved (EXTEND-OGC01 Stage 1
makes zero legal conclusions — it surfaces the statutory verb for attorney
judgment). The pattern table below IS the classifier; it is documented in
docs/OGC01-ALIGNMENT.md and evaluated against proposed gold labels.

Documented edge decision: "under regulations prescribed by the Secretary"
PRESUPPOSES authority granted elsewhere rather than granting it, so it does
NOT match any family here and such a section classifies as ``silent`` unless
another phrase grants authority. One such case is seeded in the gold set.

Precedence: statutes often contain both mandatory and discretionary grants
in one section; the classification is deterministic — any mandatory match
wins over discretionary, which wins over silent. All matches are recorded.
"""

import re

from reglens.authority.records import Classification, GrantSpan

# Verb + object vocabularies shared across families. The bounded gap
# tolerates intervening clauses without crossing sentence ends — and is
# NEGATION-FREE: an interposed "not"/"no" ("shall, notwithstanding ..., not
# prescribe", "prescribe no regulations") must never bridge into a grant.
# The deadline idiom "not later/less/more/earlier/fewer than" is NOT a
# negation ("shall, not later than 180 days ..., prescribe regulations" is a
# mandatory grant) and stays allowed. "notwithstanding" is safe by itself:
# \bnot\b requires a word boundary after "not".
_VERBS = r"(?:prescribe[sd]?|issues?d?|issue|promulgates?d?|promulgate|adopts?|establish(?:es)?)"
_OBJECTS = r"(?:regulations?|rules?\b(?:\s+and\s+regulations?)?)"
_NEG_FREE = r"(?:(?!\bno\b)(?!\bnot\b(?!\s+(?:later|less|more|earlier|fewer)\s+than))[^.;])"
_GAP = rf"{_NEG_FREE}{{0,120}}?"
_SHORT_GAP = rf"{_NEG_FREE}{{0,60}}?"

# (family label, classification, compiled pattern). Negation guards:
# "shall not"/"may not" must never match a grant family.
_FAMILIES: tuple[tuple[str, Classification, re.Pattern[str]], ...] = (
    (
        "shall-prescribe",
        Classification.mandatory,
        re.compile(
            rf"\bshall\b(?!\s+not\b){_GAP}\b{_VERBS}\b{_SHORT_GAP}\b{_OBJECTS}",
            re.IGNORECASE,
        ),
    ),
    (
        "shall-by-rule",
        Classification.mandatory,
        re.compile(
            rf"\bshall\b(?!\s+not\b){_SHORT_GAP}\bby\s+(?:rule|regulation)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "passive-shall-be-prescribed",
        Classification.mandatory,
        # Negation guards: "No regulations shall be prescribed" is a
        # prohibition, not a grant — the lookbehind and negation-free gap
        # both block it.
        re.compile(
            rf"(?<!\bno\s)\b{_OBJECTS}\b{_NEG_FREE}{{0,80}}?\bshall\s+"
            r"(?!not\b)be\s+(?:prescribed|issued|promulgated|adopted|established)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "may-prescribe",
        Classification.discretionary,
        re.compile(
            rf"\bmay\b(?!\s+not\b){_GAP}\b{_VERBS}\b{_SHORT_GAP}\b{_OBJECTS}",
            re.IGNORECASE,
        ),
    ),
    (
        "authorized-to-prescribe",
        Classification.discretionary,
        re.compile(
            rf"\bis\s+authorized\s+to\b{_GAP}\b{_VERBS}\b{_SHORT_GAP}\b{_OBJECTS}",
            re.IGNORECASE,
        ),
    ),
    (
        "may-by-rule",
        Classification.discretionary,
        re.compile(
            rf"\bmay\b(?!\s+not\b){_SHORT_GAP}\bby\s+(?:rule|regulation)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "under-such-regulations-as-may",
        Classification.discretionary,
        re.compile(
            rf"\bunder\s+such\s+{_OBJECTS}\s+as\b{_GAP}\bmay\b{_SHORT_GAP}\b{_VERBS}\b",
            re.IGNORECASE,
        ),
    ),
)

_PRECEDENCE = {
    Classification.mandatory: 0,
    Classification.discretionary: 1,
    Classification.silent: 2,
}


def find_grant_spans(section_text: str) -> list[GrantSpan]:
    """Every operative-grant match in the section text, in document order."""
    spans: list[GrantSpan] = []
    for family, classification, pattern in _FAMILIES:
        for match in pattern.finditer(section_text):
            spans.append(
                GrantSpan(
                    family=family,
                    classification=classification,
                    quote=match.group(0),
                    start=match.start(),
                    end=match.end(),
                )
            )
    spans.sort(key=lambda span: (span.start, span.end))
    return spans


def classify_section(section_text: str) -> tuple[Classification, GrantSpan | None, list[GrantSpan]]:
    """Classify one section; return (winner, winning span, all spans).

    The winning span is the earliest match of the highest-precedence
    classification. ``silent`` carries no span — there is nothing to quote,
    which is itself the finding.
    """
    spans = find_grant_spans(section_text)
    if not spans:
        return Classification.silent, None, spans
    best = min(spans, key=lambda span: (_PRECEDENCE[span.classification], span.start))
    return best.classification, best, spans
