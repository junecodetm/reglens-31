"""Memo narrative gates and deterministic reuse."""

import pytest

from reglens.memo import (
    MarkerEvidence,
    MemoDossier,
    MemoExport,
    PartMemo,
    gate_narrative,
    reusable_memo,
)

CLEAN_NARRATIVE = (
    "The deference and grounding marker families are summarized neutrally for attorney review."
)


def memo_dossier(prompt_sha256: str = "1" * 64) -> MemoDossier:
    return MemoDossier(
        provider="ollama",
        model="test-model",
        temperature=0.0,
        seed=31,
        num_ctx=8192,
        num_predict=1024,
        system_prompt_sha256="0" * 64,
        prompt_sha256=prompt_sha256,
    )


def memo_export(dossier: MemoDossier) -> MemoExport:
    memo = PartMemo(
        part=501,
        part_heading="PART 501—REPORTING",
        authority_text="Authority text for this test fixture.",
        citations=[],
        unresolved_citations=0,
        non_section_citations=0,
        markers=MarkerEvidence(
            preamble_rules=1,
            deference_count=1,
            grounding_count=1,
            deference_band="low",
            grounding_band="low",
        ),
        narrative=CLEAN_NARRATIVE,
        narrative_rejected=False,
        dossier=dossier,
    )
    return MemoExport(
        memos=[memo],
        generated=1,
        accepted=1,
        rejected=0,
        model_note="Test fixture.",
    )


def test_narrative_with_digits_is_rejected() -> None:
    assert gate_narrative(f"{CLEAN_NARRATIVE} It describes 5 rules.") == ["contains-digits"]


@pytest.mark.parametrize(
    "quoted_span",
    [
        '"agency account"',
        "“agency account”",
        "'extended agency account'",
    ],
)
def test_narrative_with_quotation_is_rejected(quoted_span: str) -> None:
    narrative = f"{CLEAN_NARRATIVE} It refers to {quoted_span}."
    assert gate_narrative(narrative) == ["contains-quotation"]


@pytest.mark.parametrize(
    "narrative",
    [
        "The agency's deference account aligns with its grounding account.",
        "The deference account isn't treated differently from the grounding account.",
    ],
)
def test_apostrophes_in_possessives_and_contractions_are_allowed(narrative: str) -> None:
    assert gate_narrative(narrative) == []


def test_fabrication_patterns_reject_narrative() -> None:
    cases: list[tuple[str, str]] = [
        ("The review describes savings of $5 million annually.", "dollar-amount"),
        ("Contact rulemaking@treasury.gov for details.", "email"),
        ("Effective January 3, 2027, this rule applies.", "calendar-date"),
        ("Assigned RIN 1505-AB12 by OIRA.", "rin"),
        ("Call (202) 555-0134 with questions.", "phone"),
        ("See https://treasury.gov/rules for details.", "url"),
    ]

    for bad, expected in cases:
        reasons = gate_narrative(f"{CLEAN_NARRATIVE} {bad}")
        assert f"fabrication:{expected}" in reasons


@pytest.mark.parametrize(
    "narrative",
    [
        "The deference marker family is summarized neutrally.",
        "The grounding marker family is summarized neutrally.",
    ],
)
def test_missing_either_marker_family_is_rejected(narrative: str) -> None:
    assert gate_narrative(narrative) == ["missing-marker-family"]


def test_clean_narrative_is_accepted() -> None:
    assert gate_narrative(CLEAN_NARRATIVE) == []


def test_reusable_memo_returns_exact_matching_prior_memo() -> None:
    dossier = memo_dossier()
    previous = memo_export(dossier)
    prior_memo = previous.memos[0]

    assert reusable_memo(previous, prior_memo.part, dossier) is prior_memo


def test_reusable_memo_rejects_mismatched_dossier() -> None:
    dossier = memo_dossier()
    previous = memo_export(dossier)
    mismatched_dossier = memo_dossier(prompt_sha256="2" * 64)

    assert reusable_memo(previous, previous.memos[0].part, mismatched_dossier) is None
