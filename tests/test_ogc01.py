"""OGC-01 eval gate: fail-closed on unavailable metrics, quotes, and regressions."""

import json
from pathlib import Path

import pytest

from reglens.eval import ogc01


@pytest.fixture
def eval_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point every module path at tmp fixtures for a minimal, healthy report."""
    authority = {
        "schema_version": 1,
        "usc_release_point": "119-102",
        "generated_from": "test",
        "parts": [
            {
                "schema_version": 1,
                "cfr_title": 31,
                "part": 1,
                "part_heading": "PART 1—TEST",
                "ecfr_date": "2026-07-27",
                "authority_text": "Authority: 31 U.S.C. 321.",
                "part_text_sha256": "0" * 64,
                "authority_start": 0,
                "authority_end": 10,
                "citations": [
                    {
                        "raw": "31 U.S.C. 321",
                        "kind": "usc-section",
                        "usc_title": 31,
                        "usc_section": "321",
                    }
                ],
                "resolved": [
                    {
                        "usc_title": 31,
                        "usc_section": "321",
                        "identifier": "/us/usc/t31/s321",
                        "heading": "t",
                        "status": None,
                        "text_sha256": "1" * 64,
                        "classification": "discretionary",
                        "grant_spans": [],
                    }
                ],
                "unresolved": [],
                "ecfr_url": "https://www.ecfr.gov/x",
            }
        ],
        "total_section_citations": 1,
        "total_resolved": 1,
        "total_unresolved": 0,
        "total_non_section_citations": 0,
        "gate_rejections": 0,
    }
    gold_auth = tmp_path / "gold-authority"
    gold_ground = tmp_path / "gold-grounding"
    gold_auth.mkdir()
    gold_ground.mkdir()
    link = {
        "part": 1,
        "usc_title": 31,
        "usc_section": "321",
        "proposed_by": "test",
        "adjudicated": False,
    }
    (gold_auth / "links_gold.jsonl").write_text(json.dumps(link) + "\n")
    (gold_auth / "links_pass1.jsonl").write_text(json.dumps(link) + "\n")
    (gold_auth / "links_pass2.jsonl").write_text(json.dumps(link) + "\n")
    cls = {
        "pair_id": "t31-s321",
        "usc_title": 31,
        "usc_section": "321",
        "classification": "discretionary",
        "proposed_by": "test",
        "adjudicated": False,
    }
    (gold_auth / "class_gold.jsonl").write_text(json.dumps(cls) + "\n")
    (gold_auth / "class_pass1.jsonl").write_text(json.dumps(cls) + "\n")
    (gold_auth / "class_pass2.jsonl").write_text(json.dumps(cls) + "\n")
    judgment = {
        "kind": "judgment",
        "document_number": "D-1",
        "family": "as-required-by",
        "start": 0,
        "end": 5,
        "genuine": True,
        "proposed_by": "test",
        "adjudicated": False,
    }
    (gold_ground / "gold.jsonl").write_text(json.dumps(judgment) + "\n")

    authority_json = tmp_path / "authority.json"
    authority_json.write_text(json.dumps(authority))
    grounding_json = tmp_path / "grounding.json"
    grounding_json.write_text(json.dumps({"total_gate_rejections": 0}))
    conformance_json = tmp_path / "conformance.json"
    conformance_json.write_text(
        json.dumps({"generated": 1, "accepted": 1, "pass_rate": 1.0, "total_unverified_quotes": 0})
    )
    monkeypatch.setattr(ogc01, "AUTHORITY_JSON", authority_json)
    monkeypatch.setattr(ogc01, "GROUNDING_JSON", grounding_json)
    monkeypatch.setattr(ogc01, "CONFORMANCE_JSON", conformance_json)
    monkeypatch.setattr(ogc01, "GOLD_AUTHORITY", gold_auth)
    monkeypatch.setattr(ogc01, "GOLD_GROUNDING", gold_ground)
    monkeypatch.setattr(ogc01, "OUT_JSON", tmp_path / "out.json")
    monkeypatch.setattr(ogc01, "BASELINE_PATH", tmp_path / "baseline.json")
    return tmp_path


def test_healthy_report_gates_clean(eval_paths: Path) -> None:
    assert ogc01.main(["--update-baseline"]) == 0
    assert ogc01.main(["--gate"]) == 0
    report = ogc01.build_report()
    assert report.link_f1 == 1.0 and report.class_accuracy == 1.0
    # Identical passes → union kappa undefined, agreement reported instead.
    assert report.link_kappa is None and report.link_pass_agreement == 1.0
    assert report.total_gold_count == 3 and report.adjudicated_count == 0
    assert report.provisional_label.startswith("Provisional — machine-proposed labels")


def test_gate_fails_closed_on_missing_gold(eval_paths: Path) -> None:
    assert ogc01.main(["--update-baseline"]) == 0
    (ogc01.GOLD_AUTHORITY / "class_gold.jsonl").unlink()
    # class_accuracy becomes None → the gate must fail, never skip.
    assert ogc01.main(["--gate"]) == 1


def test_gate_fails_on_unverified_quotes(eval_paths: Path) -> None:
    ogc01.CONFORMANCE_JSON.write_text(
        json.dumps({"generated": 1, "accepted": 1, "pass_rate": 1.0, "total_unverified_quotes": 2})
    )
    assert ogc01.main(["--gate"]) == 1


def test_gate_fails_on_regression_and_missing_floor(eval_paths: Path) -> None:
    ogc01.BASELINE_PATH.write_text(
        json.dumps(
            {
                "link_f1": 1.0,
                "class_accuracy": 1.0,
                "marker_precision": 1.0,
                "draft_pass_rate": 1.0,
            }
        )
    )
    ogc01.CONFORMANCE_JSON.write_text(
        json.dumps({"generated": 2, "accepted": 1, "pass_rate": 0.5, "total_unverified_quotes": 0})
    )
    assert ogc01.main(["--gate"]) == 1  # 0.5 < 1.0 - 0.05

    # A missing baseline floor must fail closed, not silently disarm.
    ogc01.CONFORMANCE_JSON.write_text(
        json.dumps({"generated": 1, "accepted": 1, "pass_rate": 1.0, "total_unverified_quotes": 0})
    )
    ogc01.BASELINE_PATH.write_text(json.dumps({"link_f1": 1.0}))
    assert ogc01.main(["--gate"]) == 1
