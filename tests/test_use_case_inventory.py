"""Tests for the Treasury AI Use Case Inventory parse + export path."""

import json
from pathlib import Path

import pytest

from reglens.config import Settings
from reglens.store.export_web import INVENTORY_SNAPSHOT_SHA256, export_use_case_inventory
from reglens.use_case_inventory import parse_inventory_csv

REPO_ROOT = Path(__file__).parents[1]
SNAPSHOT_CSV = (
    REPO_ROOT / "data" / "raw" / INVENTORY_SNAPSHOT_SHA256 / "Treasury-AI-Use-Case-Inventory.csv"
)

_BAND = "SECTION 1: Use Case Identifiers." + "," * 5
_HEADERS = (
    "Use Case ID,Use Case Name,Bureau/Component,Stage of Development,"
    '"Is the AI use case high-impact?",Describe the AI system\u2019s outputs.'
)


def _csv(*data_rows: str) -> bytes:
    return "\n".join([_BAND, _HEADERS, *data_rows]).encode("utf-8")


def test_parse_extracts_verbatim_row_in_column_order() -> None:
    """The OGC-01 row maps verbatim headers to verbatim values, in order."""
    content = _csv(
        "1,OCC.Chat,Office of the Comptroller of the Currency (OCC),Deployed,No,Chat answers ",
        "OGC-01,Regulatory Reform Tool,General Counsel,Pre-Deployment,High-impact, Draft rules ",
    )

    result = parse_inventory_csv(content)

    assert list(result.row) == [
        "Use Case ID",
        "Use Case Name",
        "Bureau/Component",
        "Stage of Development",
        "Is the AI use case high-impact?",
        "Describe the AI system\u2019s outputs.",
    ]
    # Verbatim: surrounding whitespace in source values is preserved.
    assert result.row["Describe the AI system\u2019s outputs."] == " Draft rules "
    assert result.context.total_use_cases == 2
    assert [entry.use_case_id for entry in result.context.high_impact] == ["OGC-01"]
    assert result.context.general_counsel_use_case_ids == ["OGC-01"]


@pytest.mark.parametrize(
    "data_rows",
    [
        (),  # no data rows at all
        ("1,Tool,IRS,Deployed,No,Text",),  # OGC-01 row absent
        (  # OGC-01 duplicated
            "OGC-01,Regulatory Reform Tool,General Counsel,Pre-Deployment,High-impact,Rules",
            "OGC-01,Regulatory Reform Tool,General Counsel,Pre-Deployment,High-impact,Rules",
        ),
        ("OGC-01,Regulatory Reform Tool,General Counsel",),  # ragged row
    ],
)
def test_parse_fails_closed_on_structural_drift(data_rows: tuple[str, ...]) -> None:
    """Missing, duplicated, or ragged rows raise instead of guessing."""
    with pytest.raises(ValueError):
        parse_inventory_csv(_csv(*data_rows))


def test_parse_requires_the_expected_header_row() -> None:
    """A restructured file without the known headers is refused."""
    content = b"SECTION 1,\nSomething,Else\nOGC-01,Regulatory Reform Tool\n"
    with pytest.raises(ValueError, match="required column header"):
        parse_inventory_csv(content)


@pytest.mark.skipif(not SNAPSHOT_CSV.is_file(), reason="committed inventory snapshot is absent")
def test_committed_snapshot_backs_the_about_section_claims() -> None:
    """The pinned snapshot yields exactly the facts the About copy states."""
    result = parse_inventory_csv(SNAPSHOT_CSV.read_bytes())

    assert result.context.total_use_cases == 129
    assert result.context.general_counsel_use_case_ids == ["OGC-01"]
    assert {entry.use_case_id for entry in result.context.high_impact} == {
        "OGC-01",
        "TREAS-IRS-104",
        "TREAS-IRS-37",
        "TREAS-IRS-46",
    }
    assert result.row["Use Case Name"] == "Regulatory Reform Tool"
    assert result.row["AI Classification"] == "Generative AI"
    # The source file's own typo is preserved verbatim (flagged [sic] in the UI).
    assert "Looper Bright" in result.row["Describe the AI system\u2019s outputs."]


@pytest.mark.skipif(not SNAPSHOT_CSV.is_file(), reason="committed inventory snapshot is absent")
def test_export_writes_pinned_provenance(tmp_path: Path) -> None:
    """The exporter publishes provenance matching the pinned snapshot."""
    web_dir = tmp_path / "web"
    (web_dir / "public" / "data").mkdir(parents=True)

    export_use_case_inventory(Settings(data_dir=REPO_ROOT / "data"), web_dir)

    payload = json.loads((web_dir / "public" / "data" / "use-case-inventory.json").read_text())
    assert payload["sha256"] == INVENTORY_SNAPSHOT_SHA256
    assert payload["source_url"].startswith("https://home.treasury.gov/")
    assert payload["row"]["Use Case ID"] == "OGC-01"
    assert payload["context"]["total_use_cases"] == 129
