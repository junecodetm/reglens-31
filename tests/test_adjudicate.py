"""Adjudication worklists render batches, progress, and failures exactly."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from reglens.eval import ogc01
from reglens.eval.adjudicate import BATCH_SIZE, render_ogc01_worklist, render_worklist
from reglens.eval.gold_records import GoldRecord
from reglens.eval.ogc01 import ClassRecord, LinkRecord, MarkerJudgment
from reglens.eval.provisions import Provision

EXPECTED_TRUNCATION_LIMIT = 400


def _provision(provision_id: str, text: str = "Synthetic provision.") -> Provision:
    return Provision(
        provision_id=provision_id,
        document_number="DOC-1",
        document_sha256="0" * 64,
        start=0,
        end=len(text),
        text=text,
    )


def _gold(provision_id: str, *, adjudicated: bool = False) -> GoldRecord:
    return GoldRecord(
        provision_id=provision_id,
        is_obligation=False,
        rationale="Synthetic rationale.",
        proposed_by="test",
        adjudicated=adjudicated,
    )


def _write_case(
    gold_dir: Path,
    provisions: Sequence[Provision],
    records: Sequence[GoldRecord],
) -> None:
    gold_dir.mkdir()
    (gold_dir / "provisions.jsonl").write_text(
        "".join(f"{provision.model_dump_json()}\n" for provision in provisions)
    )
    (gold_dir / "gold.jsonl").write_text(
        "".join(f"{record.model_dump_json()}\n" for record in records)
    )


@pytest.fixture
def ogc01_gold_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    authority_dir = tmp_path / "authority"
    grounding_dir = tmp_path / "grounding"
    authority_dir.mkdir()
    grounding_dir.mkdir()

    class_record = ClassRecord(
        pair_id="t12-s1817",
        usc_title=12,
        usc_section="1817",
        classification="operative_grant",
        verb_quote="may prescribe regulations",
        rationale="The section grants rulemaking authority.",
        proposed_by="fixture-classifier",
        adjudicated=True,
    )
    link_record = LinkRecord(
        part=501,
        usc_title=12,
        usc_section="1817",
        proposed_by="fixture-linker",
    )
    grounding_record = MarkerJudgment(
        kind="judgment",
        document_number="2026-12345",
        family="judicial_review",
        start=10,
        end=36,
        genuine=True,
        quote="subject to judicial review",
        rationale="The phrase marks reviewability.",
        proposed_by="fixture-grounder",
        adjudicated=True,
    )

    (authority_dir / "class_gold.jsonl").write_text(class_record.model_dump_json() + "\n")
    (authority_dir / "links_gold.jsonl").write_text(link_record.model_dump_json() + "\n")
    (grounding_dir / "gold.jsonl").write_text(grounding_record.model_dump_json() + "\n")
    monkeypatch.setattr(ogc01, "GOLD_AUTHORITY", authority_dir)
    monkeypatch.setattr(ogc01, "GOLD_GROUNDING", grounding_dir)


def test_render_ogc01_worklist_renders_each_fixture_backed_section_exactly(
    ogc01_gold_files: None,
) -> None:
    assert render_ogc01_worklist() == (
        "\n"
        "# OGC-01 Capability Adjudication Worklist\n"
        "\n"
        "Provisional — machine-proposed labels, human-adjudicated: 2/3.\n"
        "Apply the same protocol as above:\n"
        'find the record in its JSONL file, correct if needed, set `"adjudicated": true`,\n'
        "commit; `just eval` restates the metrics and their label automatically.\n"
        "\n"
        "## A. Classifications (1 items) — "
        "`reglens/eval/gold/authority/class_gold.jsonl`\n"
        "\n"
        "Check each against the U.S.C. section text (`web/public/data/usc/"
        "usc-<title>-s<section>.txt`) and the OGC-01 addendum in "
        "docs/ANNOTATION_GUIDELINES.md.\n"
        "\n"
        "### Batch A1\n"
        "\n"
        "1. ✅ `t12-s1817` — proposed **operative_grant** (fixture-classifier); "
        "The section grants rulemaking authority.\n"
        "\n"
        "## B. Citation pairs (1 items) — "
        "`reglens/eval/gold/authority/links_gold.jsonl`\n"
        "\n"
        "Check each (part → title, section) pair against the verbatim authority line\n"
        "shown in the Statutory authority UI section (or the eCFR).\n"
        "\n"
        "## C. Grounding markers (1 items) — "
        "`reglens/eval/gold/grounding/gold.jsonl`\n"
        "\n"
        "For `judgment` records: confirm the genuine/not-genuine call in document\n"
        "context. For `missed` records: confirm the occurrence exists and name its family.\n"
        "\n"
    )


def test_batch_headers_mark_documented_indices_and_short_final_range(tmp_path: Path) -> None:
    total = BATCH_SIZE * 2 + 5
    provisions = [_provision(f"p-{index}") for index in range(1, total + 1)]
    records = [_gold(provision.provision_id) for provision in provisions]
    gold_dir = tmp_path / "gold"
    _write_case(gold_dir, provisions, records)

    lines = render_worklist(gold_dir).splitlines()
    headers = [line for line in lines if line.startswith("## Batch ")]

    assert headers == [
        "## Batch 1 (items 1-20)",
        "## Batch 2 (items 21-40)",
        "## Batch 3 (items 41-45)",
    ]
    for header, item_number in zip(headers, (1, 21, 41), strict=True):
        header_index = lines.index(header)
        assert lines[header_index + 2].startswith(f"### {item_number}. ")


def test_progress_line_counts_only_adjudicated_records(tmp_path: Path) -> None:
    provisions = [_provision(f"p-{index}") for index in range(3)]
    records = [
        _gold("p-0", adjudicated=True),
        _gold("p-1"),
        _gold("p-2", adjudicated=True),
    ]
    gold_dir = tmp_path / "gold"
    _write_case(gold_dir, provisions, records)

    progress_line = next(
        line for line in render_worklist(gold_dir).splitlines() if line.startswith("Provisional")
    )

    assert progress_line == ("Provisional — machine-proposed labels, human-adjudicated: 2/3.")


def test_long_provision_text_is_truncated_with_one_ellipsis(tmp_path: Path) -> None:
    long_text = "x" * (EXPECTED_TRUNCATION_LIMIT + 1)
    provision = _provision("p-long", text=long_text)
    gold_dir = tmp_path / "gold"
    _write_case(gold_dir, [provision], [_gold(provision.provision_id)])

    provision_line = next(
        line
        for line in render_worklist(gold_dir).splitlines()
        if line.startswith("- **Provision:**")
    )

    assert provision_line == f"- **Provision:** {'x' * EXPECTED_TRUNCATION_LIMIT}…"


def test_orphan_gold_provision_id_raises_instead_of_being_skipped(tmp_path: Path) -> None:
    gold_dir = tmp_path / "gold"
    _write_case(gold_dir, [], [_gold("missing-id")])

    with pytest.raises(KeyError) as exc_info:
        render_worklist(gold_dir)

    assert exc_info.value.args == ("missing-id",)
