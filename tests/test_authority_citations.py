"""Citation grammar + operative-grant classifier on real authority-line forms."""

import pytest

from reglens.authority.citations import (
    AuthorityParseError,
    extract_authority_text,
    locate_authority_span,
    parse_authority,
)
from reglens.authority.classify import classify_section, find_grant_spans
from reglens.authority.records import CitationKind, Classification

PART_501 = (
    "Authority: 8 U.S.C. 1189; 18 U.S.C. 2332d, 2339B; 19 U.S.C. 3901-3913; "
    "21 U.S.C. 1901-1908; 22 U.S.C. 287c, 2370(a), 6009, 6032, 7205, 8501-8551; "
    "31 U.S.C. 321(b); 50 U.S.C. 1701-1706, 4301-4341; "
    "Pub. L. 101-410, 104 Stat. 890, as amended (28 U.S.C. 2461 note)."
)
PART_50 = (
    "Authority: 5 U.S.C. 301; 31 U.S.C. 321; Title I, Pub. L. 107-297, 116 Stat. 2322, "
    "as amended by Pub. L. 109-144, 119 Stat. 2660 (15 U.S.C. 6701 note); "
    "Pub. L. 114-74, 129 Stat. 601, Title VII (28 U.S.C. 2461 note)."
)
PART_285 = (
    "Authority: 5 U.S.C. 5514; 26 U.S.C. 6402; 31 U.S.C. 321, 3701, 3711, 3716, 3719, "
    "3720A, 3720B, 3720D; 42 U.S.C. 664; E.O. 13019, 61 FR 51763, 3 CFR, 1996 Comp., p. 216."
)
PART_356 = "Authority: 5 U.S.C. 301; 31 U.S.C. 3102, et seq.; 12 U.S.C. 391."


def kinds(text: str) -> dict[CitationKind, int]:
    counts: dict[CitationKind, int] = {}
    for citation in parse_authority(text):
        counts[citation.kind] = counts.get(citation.kind, 0) + 1
    return counts


def test_part_501_expansion_and_typing() -> None:
    citations = parse_authority(PART_501)
    by_kind = kinds(PART_501)
    # 1 + 2 + 13 + 8 + (5 singles + 51 range) + 1 + (6 + 41) = 128 section cites
    assert by_kind[CitationKind.usc_section] == 128
    assert by_kind[CitationKind.usc_note] == 1
    sections = {(c.usc_title, c.usc_section) for c in citations if c.usc_section}
    assert (22, "287c") in sections  # lowercase letter suffix survives
    assert (50, "1701") in sections and (50, "1706") in sections
    subsection = next(c for c in citations if c.usc_section == "321")
    assert subsection.subsection == "(b)"
    note = next(c for c in citations if c.kind is CitationKind.usc_note)
    assert (note.usc_title, note.usc_section) == (28, "2461")


def test_part_50_notes_never_become_sections() -> None:
    citations = parse_authority(PART_50)
    by_kind = kinds(PART_50)
    assert by_kind[CitationKind.usc_section] == 2  # 5 USC 301, 31 USC 321
    assert by_kind[CitationKind.usc_note] == 2  # TRIA + inflation-adjustment act
    # The TRIA cite must be typed usc_note: codified 15 U.S.C. 6701 is a
    # different statute and must never be quoted for this citation.
    assert any(
        c.kind is CitationKind.usc_note and (c.usc_title, c.usc_section) == (15, "6701")
        for c in citations
    )


def test_part_285_letter_suffix_and_eo() -> None:
    by_kind = kinds(PART_285)
    assert by_kind[CitationKind.usc_section] == 11
    assert by_kind[CitationKind.executive_order] == 1
    citations = parse_authority(PART_285)
    assert any(c.usc_section == "3720A" for c in citations)


def test_part_356_et_seq_binds_to_anchor() -> None:
    citations = parse_authority(PART_356)
    anchor = next(c for c in citations if c.usc_section == "3102")
    assert anchor.et_seq is True
    assert kinds(PART_356)[CitationKind.usc_section] == 3


def test_implausible_range_fails_closed() -> None:
    with pytest.raises(AuthorityParseError):
        parse_authority("Authority: 31 U.S.C. 100-9999.")


def test_unknown_segment_fails_closed() -> None:
    with pytest.raises(AuthorityParseError):
        parse_authority("Authority: the Secretary's inherent powers.")


def test_extract_authority_text_and_missing_auth() -> None:
    xml = b"<DIV5><AUTH><HED>Authority:</HED><PSPACE>5 U.S.C. 301.</PSPACE></AUTH></DIV5>"
    assert extract_authority_text(xml) == "Authority: 5 U.S.C. 301."
    with pytest.raises(LookupError):
        extract_authority_text(b"<DIV5><SOURCE/></DIV5>")


def test_locate_authority_span_gate() -> None:
    text = "Preamble words. Authority: 5 U.S.C. 301. More words."
    start, end = locate_authority_span(text, "Authority: 5 U.S.C. 301.")
    assert text[start:end] == "Authority: 5 U.S.C. 301."
    with pytest.raises(LookupError):
        locate_authority_span(text, "Authority: 99 U.S.C. 999.")


# --- classifier ---


def test_mandatory_with_intervening_clause() -> None:
    text = (
        "The Secretary shall, not later than 180 days after the date of "
        "enactment of this Act, prescribe regulations to carry out this section."
    )
    classification, span, _ = classify_section(text)
    assert classification is Classification.mandatory
    assert span is not None and span.quote.startswith("shall")
    assert text[span.start : span.end] == span.quote


def test_negation_guards() -> None:
    assert classify_section("The Secretary shall not prescribe regulations.")[0] is (
        Classification.silent
    )
    assert classify_section("The Secretary may not issue rules under this part.")[0] is (
        Classification.silent
    )


def test_passive_mandatory_form() -> None:
    classification, _, _ = classify_section(
        "Such regulations shall be prescribed by the Secretary of the Treasury."
    )
    assert classification is Classification.mandatory


def test_presupposition_is_silent() -> None:
    # Documented edge decision: presupposes authority granted elsewhere.
    classification, span, spans = classify_section(
        "Deposits shall be made under regulations prescribed by the Secretary."
    )
    assert classification is Classification.silent
    assert span is None and spans == []


def test_precedence_mandatory_beats_discretionary() -> None:
    text = (
        "The Secretary may issue rules governing minor matters. "
        "The Secretary shall prescribe regulations to implement this chapter."
    )
    classification, span, spans = classify_section(text)
    assert classification is Classification.mandatory
    assert span is not None and "shall prescribe regulations" in span.quote
    assert {s.classification for s in spans} == {
        Classification.mandatory,
        Classification.discretionary,
    }


def test_under_such_regulations_as_may_prescribe() -> None:
    classification, _, _ = classify_section(
        "Funds may be withdrawn under such regulations as the Secretary may prescribe."
    )
    assert classification is Classification.discretionary


def test_all_spans_recorded_in_document_order() -> None:
    text = (
        "The Secretary shall issue regulations under this section. "
        "The Board may prescribe rules for hearings."
    )
    spans = find_grant_spans(text)
    assert [s.classification for s in spans] == [
        Classification.mandatory,
        Classification.discretionary,
    ]
    assert spans[0].start < spans[1].start
