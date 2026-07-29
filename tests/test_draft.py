"""Skeleton template + conformance gates: structure passes, fabrication rejects."""

from reglens.authority.records import PartAuthority
from reglens.draft.conformance import (
    check_draft,
    scan_fabrication,
    verify_narrative_quotes,
)
from reglens.draft.templates import PLACEHOLDER, build_skeleton

AUTHORITY = "Authority: 5 U.S.C. 301; 31 U.S.C. 321."


def record() -> PartAuthority:
    return PartAuthority(
        part=501,
        part_heading="PART 501—REPORTING, PROCEDURES AND PENALTIES REGULATIONS",
        ecfr_date="2026-07-27",
        authority_text=AUTHORITY,
        part_text_sha256="0" * 64,
        authority_start=0,
        authority_end=len(AUTHORITY),
        citations=[],
        resolved=[],
        unresolved=[],
        ecfr_url="https://www.ecfr.gov/on/2026-07-27/title-31/part-501",
    )


CLEAN_NARRATIVE = (
    "This part concerns reporting and procedures. This skeleton provides "
    "structure only for attorney completion."
)
CORPUS = [AUTHORITY, "The Secretary shall administer the reporting requirements of this part."]


def build(doc_type: str = "nprm") -> str:
    return build_skeleton(record(), doc_type, CLEAN_NARRATIVE, CLEAN_NARRATIVE)


def test_clean_skeleton_passes_all_checks() -> None:
    for doc_type in ("nprm", "final"):
        draft = build(doc_type)
        checklist = check_draft(501, doc_type, draft, CLEAN_NARRATIVE, CORPUS)
        assert checklist.passed, checklist.model_dump()
        assert checklist.unverified_quote_count == 0


def test_template_itself_contains_no_fabrication_triggers() -> None:
    # The deterministic template must never trip the narrative scanner.
    assert scan_fabrication(build()) == []


def test_fabricated_narrative_rejects_draft() -> None:
    for bad, expected in [
        ("The rule saves $5 million annually.", "dollar-amount"),
        ("Contact rulemaking@treasury.gov for details.", "email"),
        ("Effective January 3, 2027, this rule applies.", "calendar-date"),
        ("Assigned RIN 1505-AB12 by OIRA.", "rin"),
        ("Call (202) 555-0134 with questions.", "phone"),
    ]:
        narrative = f"{CLEAN_NARRATIVE} {bad}"
        checklist = check_draft(501, "nprm", build(), narrative, CORPUS)
        assert not checklist.passed
        assert expected in checklist.fabrication_hits


def test_unverifiable_quote_rejects_and_curly_quotes_fold() -> None:
    fabricated = f'{CLEAN_NARRATIVE} The statute says "all persons must file annual reports".'
    assert verify_narrative_quotes(fabricated, CORPUS) == 1
    checklist = check_draft(501, "nprm", build(), fabricated, CORPUS)
    assert not checklist.passed and checklist.unverified_quote_count == 1

    real = (
        f"{CLEAN_NARRATIVE} The statute provides that "
        "\u201cThe Secretary shall administer the reporting requirements\u201d here."
    )
    assert verify_narrative_quotes(real, CORPUS) == 0


def test_tampered_setout_text_fails_closed() -> None:
    draft = build().replace(AUTHORITY, "Authority: 99 U.S.C. 999 (fabricated).")
    checklist = check_draft(501, "nprm", draft, CLEAN_NARRATIVE, CORPUS)
    assert not checklist.setout_text_verified and not checklist.passed


def test_silently_filled_placeholder_fails_closed() -> None:
    draft = build()
    index = draft.find("Regulatory Flexibility Act")
    window = draft[index : index + 600]
    draft = (
        draft[:index] + window.replace(PLACEHOLDER, "No impact expected.") + draft[index + 600 :]
    )
    checklist = check_draft(501, "nprm", draft, CLEAN_NARRATIVE, CORPUS)
    assert not checklist.placeholders_intact and not checklist.passed


def test_missing_heading_fails_closed() -> None:
    draft = build().replace("DATES:", "TIMING:")
    checklist = check_draft(501, "nprm", draft, CLEAN_NARRATIVE, CORPUS)
    assert not checklist.headings_in_order and not checklist.passed
