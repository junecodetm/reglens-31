"""Document grouping is derived from snapshot metadata, not a hand-maintained list.

The expected values below are the categories that were previously pinned by hand
for the original 25-document corpus. They are written out literally so this test
proves the derivation reproduces the curator's judgement rather than merely
agreeing with itself.
"""

from collections.abc import Mapping

from reglens.store.export_web import CATEGORY_ORDER, document_category

CFR_PARTS_TEXT, OFAC, IRS, OTHER = CATEGORY_ORDER


def _ref(title: int, part: str | None = None, chapter: str | None = None) -> Mapping[str, object]:
    return {"title": title, "part": part, "chapter": chapter}


def test_cfr_part_texts_group_together() -> None:
    for part in (50, 223, 285, 356, 501):
        assert document_category(f"31-CFR-{part}", []) == CFR_PARTS_TEXT


def test_ofac_is_recognised_by_chapter_or_part_range() -> None:
    """The Federal Register populates chapter OR part depending on the rule."""
    assert document_category("2026-15112", [_ref(31, chapter="V")]) == OFAC
    for part in ("501", "510", "528", "544", "560", "578", "591"):
        assert document_category("2026-00001", [_ref(31, part=part)]) == OFAC


def test_title_31_parts_outside_chapter_v_are_not_ofac() -> None:
    for part in ("50", "223", "285", "356", "499"):
        assert document_category("2026-00002", [_ref(31, part=part)]) != OFAC


def test_tax_rules_are_title_26_only() -> None:
    assert document_category("2026-13830", [_ref(26, part="1")]) == IRS


def test_joint_agency_rules_touching_title_26_are_not_tax_rules() -> None:
    """A joint OPM/Treasury/DOL rule is not an IRS regulation just because it cites title 26."""
    joint = [_ref(5, part="890"), _ref(26, part="54"), _ref(29, part="2590")]

    assert document_category("2026-11140", joint) == OTHER


def test_an_unknown_document_still_receives_a_category() -> None:
    """Total by construction: a new document must never fail the export."""
    assert document_category("2030-99999", []) == OTHER


def test_derivation_reproduces_the_previously_pinned_corpus() -> None:
    """Regression lock against the hand-maintained table this replaced."""
    previously_pinned = {
        "31-CFR-50": CFR_PARTS_TEXT,
        "31-CFR-223": CFR_PARTS_TEXT,
        "31-CFR-285": CFR_PARTS_TEXT,
        "31-CFR-356": CFR_PARTS_TEXT,
        "31-CFR-501": CFR_PARTS_TEXT,
        "2026-09090": OFAC,
        "2026-09092": OFAC,
        "2026-09094": OFAC,
        "2026-11592": OFAC,
        "2026-11601": OFAC,
        "2026-11614": OFAC,
        "2026-11615": OFAC,
        "2026-11616": OFAC,
        "2026-11761": OFAC,
        "2026-15112": OFAC,
        "2026-10116": IRS,
        "2026-13830": IRS,
        "2026-13851": IRS,
        "2026-13925": IRS,
        "2026-15008": IRS,
        "2026-10036": OTHER,
        "C1-2026-10036": OTHER,
        "2026-10037": OTHER,
        "2026-11140": OTHER,
        "2026-12787": OTHER,
    }
    from pathlib import Path

    from reglens.store.export_web import cfr_references_by_document

    references = cfr_references_by_document(Path("data"))
    derived = {
        number: document_category(number, references.get(number, []))
        for number in previously_pinned
    }

    assert derived == previously_pinned
