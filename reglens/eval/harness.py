"""Evaluation harness: pipeline outputs vs the provisional gold set.

Inputs: ``reglens/eval/gold/provisions.jsonl`` + ``gold.jsonl`` (+ optional
``pass2.jsonl`` for agreement), and ``data/processed/claims.json``. Outputs: an
:class:`EvalReport` written to ``web/public/data/eval.json``. Failure mode:
missing inputs raise; the CI gate (``--gate``) exits non-zero if F1 regresses
below the committed baseline minus tolerance or citation fidelity is not 1.0.

Honesty invariant: while any gold record has ``adjudicated == False``, every
rendered metric carries the Provisional label with the live adjudicated count.
"""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from reglens.config import Settings
from reglens.eval.gold_records import load_jsonl, load_provisions
from reglens.eval.metrics import (
    binary_icc,
    clustered_bootstrap_ci,
    cohens_kappa,
    design_effect,
    effective_sample_size,
    precision_recall_f1,
    wilson_interval,
)
from reglens.extract.run import discover_documents
from reglens.provenance import verify_span

GOLD_DIR = Path("reglens/eval/gold")
BASELINE_PATH = Path("reglens/eval/baseline.json")
F1_TOLERANCE = 0.05

Outcome = tuple[bool, bool]  # (gold_is_obligation, pipeline_predicted)


class EvalReport(BaseModel):
    """Everything the eval page and the CI gate need, in one record."""

    n_provisions: int
    n_documents: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    f1: float
    precision_wilson: tuple[float, float]
    recall_wilson: tuple[float, float]
    precision_bootstrap: tuple[float, float]
    recall_bootstrap: tuple[float, float]
    f1_bootstrap: tuple[float, float]
    kappa_pass1_pass2: float | None
    citation_fidelity: float
    icc: float
    design_effect: float
    effective_n: float
    adjudicated_count: int
    total_gold_count: int
    provisional_label: str


def _predicted_ids(claims_path: Path, provisions_path: Path) -> set[str]:
    """Provision ids overlapped by at least one gate-accepted claim."""
    extractions = json.loads(claims_path.read_text())
    spans_by_doc: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for extraction in extractions:
        for claim in extraction["claims"]:
            if claim["accepted"]:
                spans_by_doc[extraction["document_sha256"]].append((claim["start"], claim["end"]))
    predicted: set[str] = set()
    for provision in load_provisions(provisions_path).values():
        for start, end in spans_by_doc.get(provision.document_sha256, []):
            if start < provision.end and provision.start < end:
                predicted.add(provision.provision_id)
                break
    return predicted


def _f1_of(outcomes: Sequence[Outcome]) -> float:
    tp = sum(1 for gold, predicted in outcomes if gold and predicted)
    fp = sum(1 for gold, predicted in outcomes if not gold and predicted)
    fn = sum(1 for gold, predicted in outcomes if gold and not predicted)
    return precision_recall_f1(tp, fp, fn)[2]


def _precision_of(outcomes: Sequence[Outcome]) -> float:
    tp = sum(1 for gold, predicted in outcomes if gold and predicted)
    fp = sum(1 for gold, predicted in outcomes if not gold and predicted)
    return precision_recall_f1(tp, fp, 0)[0]


def _recall_of(outcomes: Sequence[Outcome]) -> float:
    tp = sum(1 for gold, predicted in outcomes if gold and predicted)
    fn = sum(1 for gold, predicted in outcomes if gold and not predicted)
    return precision_recall_f1(tp, 0, fn)[1]


def citation_fidelity(settings: Settings, claims_path: Path) -> float:
    """Re-verify every accepted claim against its source; must be 1.0 by construction."""
    texts = {pair.text_sha256: pair.text for pair in discover_documents(settings.data_dir)}
    accepted = 0
    exact = 0
    for extraction in json.loads(claims_path.read_text()):
        source = texts.get(extraction["document_sha256"])
        for claim in extraction["claims"]:
            if claim["accepted"]:
                accepted += 1
                if source is not None and verify_span(source, claim["quote"]).accepted:
                    exact += 1
    return exact / accepted if accepted else 1.0


def build_report(settings: Settings, claims_path: Path, gold_dir: Path = GOLD_DIR) -> EvalReport:
    provisions = load_provisions(gold_dir / "provisions.jsonl")
    gold = load_jsonl(gold_dir / "gold.jsonl")
    predicted = _predicted_ids(claims_path, gold_dir / "provisions.jsonl")

    by_document: dict[str, list[Outcome]] = defaultdict(list)
    outcomes: list[Outcome] = []
    tp = fp = fn = tn = 0
    for record in gold:
        provision = provisions[record.provision_id]
        outcome = (record.is_obligation, record.provision_id in predicted)
        outcomes.append(outcome)
        by_document[provision.document_number].append(outcome)
        match outcome:
            case (True, True):
                tp += 1
            case (False, True):
                fp += 1
            case (True, False):
                fn += 1
            case (False, False):
                tn += 1

    precision, recall, f1 = precision_recall_f1(tp, fp, fn)
    clusters = list(by_document.values())
    correctness_clusters = [
        [gold_label == predicted_label for gold_label, predicted_label in cluster]
        for cluster in clusters
    ]
    icc = binary_icc(correctness_clusters)
    deff = design_effect(len(outcomes) / len(clusters), icc)

    pass2_path = gold_dir / "pass2.jsonl"
    kappa: float | None = None
    if pass2_path.is_file():
        pass2 = {record.provision_id: record.is_obligation for record in load_jsonl(pass2_path)}
        aligned = [
            (str(record.is_obligation), str(pass2[record.provision_id]))
            for record in gold
            if record.provision_id in pass2
        ]
        if aligned:
            kappa = cohens_kappa([a for a, _ in aligned], [b for _, b in aligned])

    adjudicated = sum(1 for record in gold if record.adjudicated)
    label = (
        f"Provisional — machine-proposed labels, human-adjudicated: "
        f"{adjudicated}/{len(gold)}. Metrics will be restated as adjudication proceeds."
        if adjudicated < len(gold)
        else f"Human-adjudicated gold set ({adjudicated}/{len(gold)})."
    )

    return EvalReport(
        n_provisions=len(gold),
        n_documents=len(clusters),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        precision_wilson=wilson_interval(tp, tp + fp) if tp + fp else (0.0, 0.0),
        recall_wilson=wilson_interval(tp, tp + fn) if tp + fn else (0.0, 0.0),
        precision_bootstrap=clustered_bootstrap_ci(clusters, _precision_of),
        recall_bootstrap=clustered_bootstrap_ci(clusters, _recall_of),
        f1_bootstrap=clustered_bootstrap_ci(clusters, _f1_of),
        kappa_pass1_pass2=kappa,
        citation_fidelity=citation_fidelity(settings, claims_path),
        icc=icc,
        design_effect=deff,
        effective_n=effective_sample_size(len(outcomes), deff),
        adjudicated_count=adjudicated,
        total_gold_count=len(gold),
        provisional_label=label,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens.eval.harness")
    parser.add_argument("--gate", action="store_true", help="fail on regression vs baseline")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(argv)

    settings = Settings()
    claims_path = settings.data_dir / "processed" / "claims.json"
    report = build_report(settings, claims_path)

    out_path = Path("web/public/data/eval.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report.model_dump_json(indent=2) + "\n")
    print(
        f"P={report.precision:.3f} R={report.recall:.3f} F1={report.f1:.3f} "
        f"fidelity={report.citation_fidelity:.3f} kappa={report.kappa_pass1_pass2} "
        f"[{report.provisional_label}]"
    )

    if args.update_baseline:
        BASELINE_PATH.write_text(json.dumps({"f1": report.f1}, indent=2) + "\n")
        return 0
    if args.gate:
        if report.citation_fidelity < 1.0:
            # Fail-closed guardrail: an accepted claim that no longer verifies is a defect.
            print("GATE FAIL: citation fidelity below 1.0")
            return 1
        baseline_f1 = json.loads(BASELINE_PATH.read_text())["f1"]
        if report.f1 < baseline_f1 - F1_TOLERANCE:
            print(f"GATE FAIL: F1 {report.f1:.3f} < baseline {baseline_f1:.3f} - {F1_TOLERANCE}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
