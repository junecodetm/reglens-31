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
    kappa_band,
    precision_recall_f1,
    wilson_interval,
)
from reglens.extract.records import load_extractions
from reglens.extract.run import discover_documents
from reglens.provenance import verify_span

GOLD_DIR = Path("reglens/eval/gold")
BASELINE_PATH = Path("reglens/eval/baseline.json")
F1_TOLERANCE = 0.05

Outcome = tuple[bool, bool]  # (gold_is_obligation, pipeline_predicted)


class StratumMetrics(BaseModel):
    """P/R within one sampling stratum (pooled precision is prevalence-sensitive)."""

    n: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float | None
    recall: float | None


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
    bootstrap_undefined_fractions: dict[str, float]
    kappa_pass1_pass2: float | None
    kappa_band: str | None
    kappa_note: str
    citation_fidelity: float
    icc: float
    icc_outcome: str
    design_effect: float
    effective_n: float
    strata: dict[str, StratumMetrics]
    adjudicated_count: int
    total_gold_count: int
    provisional_label: str


def _predicted_ids(claims_path: Path, provisions_path: Path) -> set[str]:
    """Provision ids overlapped by at least one gate-accepted claim."""
    spans_by_doc: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for extraction in load_extractions(claims_path):
        for claim in extraction.claims:
            if claim.accepted and claim.start is not None and claim.end is not None:
                spans_by_doc[extraction.document_sha256].append((claim.start, claim.end))
    predicted: set[str] = set()
    for provision in load_provisions(provisions_path).values():
        for start, end in spans_by_doc.get(provision.document_sha256, []):
            if start < provision.end and provision.start < end:
                predicted.add(provision.provision_id)
                break
    return predicted


def _precision_of(outcomes: Sequence[Outcome]) -> float | None:
    """None (undefined), not 0.0, when a resample has no predicted positives."""
    tp = sum(1 for gold, predicted in outcomes if gold and predicted)
    fp = sum(1 for gold, predicted in outcomes if not gold and predicted)
    return tp / (tp + fp) if tp + fp else None


def _recall_of(outcomes: Sequence[Outcome]) -> float | None:
    """None (undefined), not 0.0, when a resample has no gold positives."""
    tp = sum(1 for gold, predicted in outcomes if gold and predicted)
    fn = sum(1 for gold, predicted in outcomes if gold and not predicted)
    return tp / (tp + fn) if tp + fn else None


def _f1_of(outcomes: Sequence[Outcome]) -> float | None:
    precision = _precision_of(outcomes)
    recall = _recall_of(outcomes)
    if precision is None or recall is None:
        return None
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def citation_fidelity(settings: Settings, claims_path: Path) -> float:
    """Re-verify every accepted claim against its source; must be 1.0 by construction."""
    texts = {pair.text_sha256: pair.text for pair in discover_documents(settings.data_dir)}
    accepted = 0
    exact = 0
    for extraction in load_extractions(claims_path):
        source = texts.get(extraction.document_sha256)
        for claim in extraction.claims:
            if claim.accepted:
                accepted += 1
                if source is not None and verify_span(source, claim.quote).accepted:
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
    # Cluster sizes are unequal (the eCFR stratum samples more per document), so
    # the size-weighted mean cluster size (Σm²/Σm) is used — the conservative
    # generalization of docs/EVALUATION.md's m̄ for unequal clusters.
    sizes = [len(cluster) for cluster in clusters]
    weighted_mean_size = sum(size * size for size in sizes) / sum(sizes)
    deff = design_effect(weighted_mean_size, icc)

    # Kappa compares the two FROZEN proposal passes (different models). It must
    # never read gold.jsonl, which human adjudication mutates over time.
    pass1_path = gold_dir / "pass1.jsonl"
    pass2_path = gold_dir / "pass2.jsonl"
    kappa: float | None = None
    if pass1_path.is_file() and pass2_path.is_file():
        pass1 = {record.provision_id: record.is_obligation for record in load_jsonl(pass1_path)}
        pass2 = {record.provision_id: record.is_obligation for record in load_jsonl(pass2_path)}
        aligned = [
            (str(pass1[pid]), str(pass2[pid])) for pid in sorted(pass1.keys() & pass2.keys())
        ]
        if aligned:
            kappa = cohens_kappa([a for a, _ in aligned], [b for _, b in aligned])

    stratum_outcomes: dict[str, list[Outcome]] = defaultdict(list)
    for record in gold:
        provision = provisions[record.provision_id]
        stratum_outcomes[provision.stratum].append(
            (record.is_obligation, record.provision_id in predicted)
        )
    strata: dict[str, StratumMetrics] = {}
    for stratum_name, stratum_items in sorted(stratum_outcomes.items()):
        s_tp = sum(1 for g, p in stratum_items if g and p)
        s_fp = sum(1 for g, p in stratum_items if not g and p)
        s_fn = sum(1 for g, p in stratum_items if g and not p)
        strata[stratum_name] = StratumMetrics(
            n=len(stratum_items),
            true_positives=s_tp,
            false_positives=s_fp,
            false_negatives=s_fn,
            precision=_precision_of(stratum_items),
            recall=_recall_of(stratum_items),
        )

    adjudicated = sum(1 for record in gold if record.adjudicated)
    label = (
        f"Provisional — machine-proposed labels, human-adjudicated: "
        f"{adjudicated}/{len(gold)}. Metrics will be restated as adjudication proceeds."
        if adjudicated < len(gold)
        else f"Human-adjudicated gold set ({adjudicated}/{len(gold)})."
    )

    precision_ci = clustered_bootstrap_ci(clusters, _precision_of)
    recall_ci = clustered_bootstrap_ci(clusters, _recall_of)
    f1_ci = clustered_bootstrap_ci(clusters, _f1_of)

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
        precision_bootstrap=(precision_ci.low, precision_ci.high),
        recall_bootstrap=(recall_ci.low, recall_ci.high),
        f1_bootstrap=(f1_ci.low, f1_ci.high),
        bootstrap_undefined_fractions={
            "precision": precision_ci.undefined_fraction,
            "recall": recall_ci.undefined_fraction,
            "f1": f1_ci.undefined_fraction,
        },
        kappa_pass1_pass2=kappa,
        kappa_band=kappa_band(kappa) if kappa is not None else None,
        kappa_note=(
            "Agreement between two frozen proposal passes by different models "
            "(claude-fable-5 vs claude-sonnet-5) applying the written guidelines; "
            "human inter-annotator kappa pending adjudication."
        ),
        citation_fidelity=citation_fidelity(settings, claims_path),
        icc=icc,
        icc_outcome="correctness indicator (prediction == gold), clustered by document",
        design_effect=deff,
        effective_n=effective_sample_size(len(outcomes), deff),
        strata=strata,
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
        if not BASELINE_PATH.is_file():
            print("GATE: no committed baseline yet (fidelity enforced; F1 gate armed on commit)")
            return 0
        baseline_f1 = json.loads(BASELINE_PATH.read_text())["f1"]
        if report.f1 < baseline_f1 - F1_TOLERANCE:
            print(f"GATE FAIL: F1 {report.f1:.3f} < baseline {baseline_f1:.3f} - {F1_TOLERANCE}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
