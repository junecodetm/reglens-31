"""Eval harness on a synthetic gold set: counts, CIs, kappa, and the provisional label."""

import json
from pathlib import Path

import pytest

from reglens.config import Settings
from reglens.eval.harness import build_report
from reglens.extract.records import ClaimRecord, DocumentExtraction
from reglens.extract.schema import RunMeta
from reglens.ingest.snapshot import write_snapshot

DOC_A_TEXT = "Alpha paragraph one.\n\nEach bank must report daily.\n\nBackground history text here."
DOC_B_TEXT = (
    "Beta scope statement.\n\nNo person may export widgets.\n\nDefinitions apply to this part."
)


def _provision(document: str, sha: str, start: int, end: int, text: str, pid: str) -> str:
    return json.dumps(
        {
            "provision_id": pid,
            "document_number": document,
            "document_sha256": sha,
            "start": start,
            "end": end,
            "text": text,
        }
    )


def _gold(pid: str, is_obligation: bool) -> str:
    return json.dumps(
        {
            "provision_id": pid,
            "is_obligation": is_obligation,
            "rationale": "synthetic",
            "proposed_by": "test",
            "adjudicated": False,
        }
    )


@pytest.fixture
def eval_env(tmp_path: Path) -> tuple[Settings, Path, Path]:
    settings = Settings(data_dir=tmp_path / "data")
    docs = {"DOC-A": DOC_A_TEXT, "DOC-B": DOC_B_TEXT}
    shas: dict[str, str] = {}
    for name, text in docs.items():
        write_snapshot(
            settings.data_dir,
            source_id="federal_register",
            url=f"https://www.federalregister.gov/api/v1/documents/{name}.json",
            content=json.dumps({"document_number": name, "title": name, "html_url": ""}).encode(),
            content_type="application/json",
            filename=f"{name}.json",
        )
        text_dir = write_snapshot(
            settings.data_dir,
            source_id="federal_register",
            url=f"https://www.federalregister.gov/documents/full_text/text/{name}.txt",
            content=text.encode(),
            content_type="text/plain",
            filename=f"{name}.txt",
        )
        shas[name] = text_dir.name

    gold_dir = tmp_path / "gold"
    gold_dir.mkdir()
    # Provisions: A1 = the obligation sentence in DOC-A; A2 = background (negative);
    # B1 = the prohibition in DOC-B (pipeline will miss it -> FN); B2 = definitions (negative).
    a_ob_start = DOC_A_TEXT.index("Each bank")
    a_ob_end = a_ob_start + len("Each bank must report daily.")
    b_ob_start = DOC_B_TEXT.index("No person")
    b_ob_end = b_ob_start + len("No person may export widgets.")
    provisions = [
        _provision(
            "DOC-A", shas["DOC-A"], a_ob_start, a_ob_end, "Each bank must report daily.", "p-a1"
        ),
        _provision("DOC-A", shas["DOC-A"], 55, 80, "Background history text", "p-a2"),
        _provision(
            "DOC-B", shas["DOC-B"], b_ob_start, b_ob_end, "No person may export widgets.", "p-b1"
        ),
        _provision("DOC-B", shas["DOC-B"], 55, 85, "Definitions apply", "p-b2"),
    ]
    (gold_dir / "provisions.jsonl").write_text("\n".join(provisions) + "\n")
    gold_lines = "\n".join(
        [_gold("p-a1", True), _gold("p-a2", False), _gold("p-b1", True), _gold("p-b2", False)]
    )
    (gold_dir / "gold.jsonl").write_text(gold_lines + "\n")
    # Kappa compares the FROZEN passes; pass 2 disagrees on one of four -> kappa = 0.5.
    (gold_dir / "pass1.jsonl").write_text(gold_lines + "\n")
    (gold_dir / "pass2.jsonl").write_text(
        "\n".join(
            [_gold("p-a1", True), _gold("p-a2", False), _gold("p-b1", True), _gold("p-b2", True)]
        )
        + "\n"
    )

    claims_path = tmp_path / "claims.json"
    quote = "Each bank must report daily."
    run = RunMeta(model_tag="fake", prompt_sha256="0" * 64, input_sha256="1" * 64)

    def extraction(name: str, claims: list[ClaimRecord]) -> DocumentExtraction:
        return DocumentExtraction(
            document_sha256=shas[name],
            document_number=name,
            document_title=name,
            document_url="https://www.federalregister.gov/documents/x",
            accepted_count=sum(1 for claim in claims if claim.accepted),
            rejected_count=sum(1 for claim in claims if not claim.accepted),
            total_chars=len(docs[name]),
            extracted_chars=len(docs[name]),
            claims=claims,
        )

    accepted_claim = ClaimRecord(
        claim_id="c1",
        document_sha256=shas["DOC-A"],
        document_number="DOC-A",
        document_title="DOC-A",
        document_url="https://www.federalregister.gov/documents/x",
        quote=quote,
        obligation_type="reporting",
        affected_party="banks",
        summary="Report daily.",
        effective_date=None,
        accepted=True,
        start=a_ob_start,
        end=a_ob_end,
        rejection_reason=None,
        run=run,
    )
    claims_path.write_text(
        json.dumps(
            [
                extraction("DOC-A", [accepted_claim]).model_dump(),
                extraction("DOC-B", []).model_dump(),
            ]
        )
    )
    return settings, claims_path, gold_dir


def test_report_counts_cis_kappa_and_label(eval_env: tuple[Settings, Path, Path]) -> None:
    settings, claims_path, gold_dir = eval_env
    report = build_report(settings, claims_path, gold_dir=gold_dir)

    # TP=p-a1, TN=p-a2 and p-b2, FN=p-b1, FP=0
    assert (report.true_positives, report.false_positives) == (1, 0)
    assert (report.false_negatives, report.true_negatives) == (1, 2)
    assert report.precision == 1.0
    assert report.recall == 0.5
    assert report.citation_fidelity == 1.0
    assert report.kappa_pass1_pass2 == pytest.approx(0.5)
    assert report.kappa_band == "Moderate"
    assert report.adjudicated_count == 0
    assert report.provisional_label.startswith("Provisional — machine-proposed labels")
    assert "0/4" in report.provisional_label
    low, high = report.f1_bootstrap
    assert 0.0 <= low <= report.f1 <= high <= 1.0
    assert set(report.bootstrap_undefined_fractions) == {"precision", "recall", "f1"}
    assert "base" in report.strata
    assert report.strata["base"].n == 4
