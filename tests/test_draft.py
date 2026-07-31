"""Skeleton template + conformance gates: structure passes, fabrication rejects."""

from pathlib import Path

import pytest

from reglens.authority.records import PartAuthority
from reglens.config import Settings
from reglens.draft import run as draft_run
from reglens.draft.conformance import (
    DraftChecklist,
    DraftDossier,
    check_draft,
    scan_fabrication,
    verify_narrative_quotes,
)
from reglens.draft.templates import PLACEHOLDER, build_skeleton

AUTHORITY = "Authority: 5 U.S.C. 301; 31 U.S.C. 321."
PART_TEXT = "PART 501 REPORTING\nAuthority: 5 U.S.C. 301; 31 U.S.C. 321.\n"
PART_TEXT_SHA256 = "f014d1fdaefb688790ba5fd28107b884602f309e313c5ecb952892c970927c6e"
TEST_DOSSIER = DraftDossier(
    model="test-model",
    temperature=0.0,
    seed=31,
    num_ctx=8192,
    num_predict=1024,
    system_prompt_sha256="0" * 64,
    prompt_sha256="1" * 64,
    input_sha256=PART_TEXT_SHA256,
    narrative_fields=["summary", "supplementary_intro"],
)


def record(part_text_sha256: str = "0" * 64) -> PartAuthority:
    return PartAuthority(
        part=501,
        part_heading="PART 501—REPORTING, PROCEDURES AND PENALTIES REGULATIONS",
        ecfr_date="2026-07-27",
        authority_text=AUTHORITY,
        part_text_sha256=part_text_sha256,
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
        checklist = check_draft(
            501,
            doc_type,
            draft,
            CLEAN_NARRATIVE,
            CORPUS,
            dossier=TEST_DOSSIER,
        )
        assert checklist.passed, checklist.model_dump()
        assert checklist.dossier == TEST_DOSSIER
        assert checklist.amendatory_forms_demonstrated
        assert checklist.authority_citation_present
        assert checklist.basis_and_purpose_present
        assert checklist.comment_period_reference
        assert checklist.unverified_quote_count == 0


def test_templates_demonstrate_all_amendatory_forms() -> None:
    draft = build()
    assert (
        f"2. Amend § 501.___ by adding paragraph (___) to read as follows:\n\n   {PLACEHOLDER}"
    ) in draft
    assert f"3. Revise § 501.___ to read as follows:\n\n   {PLACEHOLDER}" in draft
    assert "4. Remove and reserve § 501.___." in draft


@pytest.mark.parametrize(
    ("doc_type", "dates_line"),
    [
        ("nprm", f"DATES: Comments must be received on or before {PLACEHOLDER}."),
        ("final", f"DATES: Effective date: {PLACEHOLDER}."),
    ],
)
def test_template_dates_match_document_type(doc_type: str, dates_line: str) -> None:
    assert dates_line in build(doc_type)


@pytest.mark.parametrize(
    ("original", "mutated"),
    [
        ("Amend § 501.___ by adding paragraph", "Amend § 501.___ by inserting paragraph"),
        ("Revise § 501.___ to read as follows:", "Revise § 501.___ as follows:"),
        ("Remove and reserve § 501.___", "Remove but reserve § 501.___"),
    ],
)
def test_each_amendatory_form_is_required(original: str, mutated: str) -> None:
    draft = build().replace(original, mutated)
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert checklist.amendatory_instructions_parse
    assert not checklist.amendatory_forms_demonstrated
    assert not checklist.passed


def test_amendatory_forms_must_be_in_instruction_section() -> None:
    draft = build().replace(
        "Amend § 501.___ by adding paragraph",
        "Amend § 501.___ by inserting paragraph",
        1,
    )
    draft = draft.replace(
        "SUMMARY: [model-generated]",
        "SUMMARY: Amend § 501.___ by adding paragraph. [model-generated]",
        1,
    )
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.amendatory_forms_demonstrated
    assert not checklist.passed


def test_authority_citation_requires_nonempty_block() -> None:
    draft = build().replace(f"\n   {AUTHORITY}\n\n", "\n\n", 1)
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.authority_citation_present
    assert not checklist.passed


def test_basis_and_purpose_requires_all_structural_elements() -> None:
    draft = build().replace("   I. Background\n", "", 1)
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.basis_and_purpose_present
    assert not checklist.passed


@pytest.mark.parametrize(
    ("doc_type", "reference"),
    [
        ("nprm", "Comments must be received on or before"),
        ("final", "Effective date:"),
    ],
)
def test_comment_period_reference_matches_document_type(doc_type: str, reference: str) -> None:
    draft = build(doc_type).replace(reference, "Timing omitted", 1)
    checklist = check_draft(
        501,
        doc_type,
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.comment_period_reference
    assert not checklist.passed


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
        checklist = check_draft(
            501,
            "nprm",
            build(),
            narrative,
            CORPUS,
            dossier=TEST_DOSSIER,
        )
        assert not checklist.passed
        assert expected in checklist.fabrication_hits


def test_unverifiable_quote_rejects_and_curly_quotes_fold() -> None:
    fabricated = f'{CLEAN_NARRATIVE} The statute says "all persons must file annual reports".'
    assert verify_narrative_quotes(fabricated, CORPUS) == 1
    checklist = check_draft(
        501,
        "nprm",
        build(),
        fabricated,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.passed and checklist.unverified_quote_count == 1

    real = (
        f"{CLEAN_NARRATIVE} The statute provides that "
        "\u201cThe Secretary shall administer the reporting requirements\u201d here."
    )
    assert verify_narrative_quotes(real, CORPUS) == 0


def test_tampered_setout_text_fails_closed() -> None:
    draft = build().replace(AUTHORITY, "Authority: 99 U.S.C. 999 (fabricated).")
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.setout_text_verified and not checklist.passed


def test_same_line_tampered_setout_text_fails_closed() -> None:
    draft = build().replace(
        f"read as follows:\n\n   {AUTHORITY}",
        "read as follows: Authority: 99 U.S.C. 999 (fabricated).",
        1,
    )
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.setout_text_verified and not checklist.passed


def test_same_line_tampered_setout_with_placeholder_fails_closed() -> None:
    instruction = "2. Amend § 501.___ by adding paragraph (___) to read as follows:"
    draft = build().replace(
        f"{instruction}\n\n   {PLACEHOLDER}",
        f"{instruction} Fabricated mandatory text. {PLACEHOLDER}",
        1,
    )
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.setout_text_verified and not checklist.passed


def test_silently_filled_placeholder_fails_closed() -> None:
    draft = build()
    index = draft.find("Regulatory Flexibility Act")
    window = draft[index : index + 600]
    draft = (
        draft[:index] + window.replace(PLACEHOLDER, "No impact expected.") + draft[index + 600 :]
    )
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.placeholders_intact and not checklist.passed


def test_missing_heading_fails_closed() -> None:
    draft = build().replace("DATES:", "TIMING:")
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.headings_in_order and not checklist.passed


def test_dossier_hashes_are_stable_for_fixed_inputs() -> None:
    settings = Settings(model_tag="test-model")
    source_record = record(PART_TEXT_SHA256)
    first = draft_run.build_dossier(settings, source_record, "nprm", PART_TEXT)
    second = draft_run.build_dossier(settings, source_record, "nprm", PART_TEXT)

    assert first == second
    assert first.model_dump() == {
        "provider": "local",
        "model": "test-model",
        "temperature": 0.0,
        "seed": 31,
        "num_ctx": 8192,
        "num_predict": 1024,
        "max_tokens": None,
        "reasoning_effort": None,
        "system_prompt_sha256": (
            "016620abd0b61716d597266e2b981bbf0fbc7a0a1dd49a3aa7fa8cf718117069"
        ),
        "prompt_sha256": "a6773124a38781150dee6263f0967c02ba088e60641c3da561432a4aa68dc9e6",
        "input_sha256": PART_TEXT_SHA256,
        "narrative_fields": ["summary", "supplementary_intro"],
    }


def test_fabricated_second_setout_paragraph_fails_closed() -> None:
    draft = build().replace(
        f"read as follows:\n\n   {AUTHORITY}",
        f"read as follows:\n\n   {AUTHORITY}\n\n   Fabricated second set-out paragraph.",
        1,
    )
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.setout_text_verified and not checklist.passed


def test_extra_blank_lines_before_setout_text_fail_closed() -> None:
    draft = build().replace(
        f"read as follows:\n\n   {AUTHORITY}",
        "read as follows:\n\n\n\n   Fabricated set-out text after blank lines.",
        1,
    )
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.setout_text_verified and not checklist.passed


def test_empty_setout_region_fails_closed() -> None:
    draft = build().replace(f"read as follows:\n\n   {AUTHORITY}", "read as follows:", 1)
    checklist = check_draft(
        501,
        "nprm",
        draft,
        CLEAN_NARRATIVE,
        CORPUS,
        dossier=TEST_DOSSIER,
    )
    assert not checklist.setout_text_verified and not checklist.passed


def reusable_checklist_fixture(
    *,
    dossier: DraftDossier = TEST_DOSSIER,
    passed: bool = True,
) -> DraftChecklist:
    return DraftChecklist(
        part=501,
        doc_type="nprm",
        headings_in_order=True,
        analysis_sections_present=True,
        placeholders_intact=True,
        amendatory_instructions_parse=True,
        amendatory_forms_demonstrated=True,
        authority_citation_present=True,
        basis_and_purpose_present=True,
        comment_period_reference=True,
        setout_text_verified=True,
        narrative_fabrication_clean=passed,
        quotes_verified=True,
        unverified_quote_count=0,
        fabrication_hits=[] if passed else ["test-failure"],
        dossier=dossier,
        passed=passed,
    )


def conformance_report_fixture(checklist: DraftChecklist) -> draft_run.ConformanceReport:
    return draft_run.ConformanceReport(
        checklists=[checklist],
        generated=1,
        accepted=int(checklist.passed),
        rejected=int(not checklist.passed),
        pass_rate=1.0 if checklist.passed else 0.0,
        total_unverified_quotes=checklist.unverified_quote_count,
        rejected_drafts=[] if checklist.passed else ["31-CFR-501-nprm.txt"],
    )


def test_reusable_checklist_returns_exact_matching_checklist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(draft_run, "DRAFTS_DIR", tmp_path)
    (tmp_path / "31-CFR-501-nprm.txt").write_text("existing draft")
    checklist = reusable_checklist_fixture()
    report = conformance_report_fixture(checklist)

    reused = draft_run.reusable_checklist(report, TEST_DOSSIER, 501, "nprm")

    assert reused is checklist


def test_reusable_checklist_rejects_changed_dossier() -> None:
    checklist = reusable_checklist_fixture(passed=False)
    report = conformance_report_fixture(checklist)
    changed_dossier = TEST_DOSSIER.model_copy(update={"model": "changed-model"})

    reused = draft_run.reusable_checklist(report, changed_dossier, 501, "nprm")

    assert reused is None


def test_reusable_checklist_rejects_missing_passed_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(draft_run, "DRAFTS_DIR", tmp_path)
    checklist = reusable_checklist_fixture()
    report = conformance_report_fixture(checklist)

    reused = draft_run.reusable_checklist(report, TEST_DOSSIER, 501, "nprm")

    assert reused is None


@pytest.fixture(autouse=True)
def _default_draft_tests_to_local_provider(  # pyright: ignore[reportUnusedFunction] — autouse fixture
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep implicit-provider tests isolated from a developer's dotenv file."""
    monkeypatch.setenv("REGLENS_DRAFT_PROVIDER", "local")
