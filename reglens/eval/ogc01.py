"""EXTEND-OGC01 evaluation: authority linking, classification, grounding, drafts.

Inputs: ``data/processed/{authority,grounding,conformance}.json`` plus the
frozen proposal passes and (mutable) gold files under
``reglens/eval/gold/{authority,grounding}/``. Outputs:
``web/public/data/ogc01-eval.json``. Failure mode: missing inputs raise; the
``--gate`` mode exits non-zero when a gated metric regresses below the
committed baseline minus tolerance.

Honesty invariants (BUILD.md §4, EXTEND-OGC01 §4): every metric carries the
Provisional label with the live adjudicated count; kappa is cross-model
agreement between frozen passes, never human IAA; there is NO metric of the
form "predicted judicial outcome" anywhere, by design.
"""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from reglens.authority.records import AuthorityExport
from reglens.eval.harness import Outcome, f1_of
from reglens.eval.metrics import (
    clustered_bootstrap_ci,
    cohens_kappa,
    kappa_band,
    wilson_interval,
)

GOLD_AUTHORITY = Path("reglens/eval/gold/authority")
GOLD_GROUNDING = Path("reglens/eval/gold/grounding")
AUTHORITY_JSON = Path("data/processed/authority.json")
GROUNDING_JSON = Path("data/processed/grounding.json")
CONFORMANCE_JSON = Path("data/processed/conformance.json")
OUT_JSON = Path("web/public/data/ogc01-eval.json")
BASELINE_PATH = Path("reglens/eval/ogc01_baseline.json")
TOLERANCE = 0.05

CLUSTER_CAVEAT = (
    "Census, not a sample: every citation pair from the five in-scope parts is "
    "evaluated. Clustered bootstrap runs over only 5 part-level clusters, "
    "dominated by part 501 — intervals are unstable and reported anyway."
)


class LinkRecord(BaseModel):
    """One gold (part → U.S.C. section) pair, enumerated from the authority line."""

    part: int
    usc_title: int
    usc_section: str
    proposed_by: str
    adjudicated: bool = False


class ClassRecord(BaseModel):
    """One gold operative-grant classification for a U.S.C. section."""

    pair_id: str
    usc_title: int
    usc_section: str
    classification: str
    verb_quote: str | None = None
    rationale: str = ""
    proposed_by: str
    adjudicated: bool = False


class MarkerJudgment(BaseModel):
    """One in-context judgment of a retrieved marker span (or a missed one)."""

    kind: str  # "judgment" | "missed"
    document_number: str
    family: str
    start: int | None = None
    end: int | None = None
    genuine: bool | None = None
    quote: str | None = None
    rationale: str = ""
    proposed_by: str
    adjudicated: bool = False


class Ogc01EvalReport(BaseModel):
    """Everything the eval UI section and the CI gate need."""

    # Authority linking (parser vs independently enumerated pairs)
    link_gold_count: int
    link_predicted_count: int
    link_tp: int
    link_fp: int
    link_fn: int
    link_precision: float | None
    link_recall: float | None
    link_f1: float | None
    link_precision_wilson: tuple[float, float] | None
    link_recall_wilson: tuple[float, float] | None
    link_f1_bootstrap: tuple[float, float] | None
    link_kappa: float | None
    # Classification (deterministic pattern table vs proposed gold)
    class_n: int
    class_correct: int
    class_accuracy: float | None
    class_accuracy_wilson: tuple[float, float] | None
    class_accuracy_bootstrap: tuple[float, float] | None
    class_kappa: float | None
    class_kappa_band: str | None
    # Coverage facts (not errors)
    unresolved_count: int
    unresolved_rate: float
    non_section_citations: int
    authority_gate_rejections: int
    # Grounding retrieval
    marker_judged: int
    marker_genuine: int
    marker_precision: float | None
    marker_precision_wilson: tuple[float, float] | None
    marker_missed: int
    marker_recall: float | None
    marker_recall_wilson: tuple[float, float] | None
    grounding_kappa: float | None
    grounding_gate_rejections: int
    # Draft skeletons (deterministic checklist — the only honest generation metric)
    draft_generated: int
    draft_accepted: int
    draft_pass_rate: float
    draft_unverified_quotes: int
    # Honesty labels
    kappa_note: str
    cluster_caveat: str = CLUSTER_CAVEAT
    adjudicated_count: int
    total_gold_count: int
    provisional_label: str


def load_typed_jsonl(path: Path, model: type[BaseModel]) -> list[BaseModel]:
    if not path.is_file():
        return []
    return [model.model_validate_json(line) for line in path.read_text().splitlines() if line]


def _pair_key(title: int, section: str) -> str:
    return f"t{title}-s{section}"


def build_report() -> Ogc01EvalReport:
    export = AuthorityExport.model_validate_json(AUTHORITY_JSON.read_text())
    grounding = json.loads(GROUNDING_JSON.read_text())
    conformance = json.loads(CONFORMANCE_JSON.read_text())

    # --- Authority linking: predicted pairs per part vs gold pairs per part.
    predicted: set[tuple[int, int, str]] = set()
    part_of_pair: dict[tuple[int, str], int] = {}
    for part in export.parts:
        for citation in part.citations:
            if citation.kind.value == "usc-section" and citation.usc_section:
                assert citation.usc_title is not None
                predicted.add((part.part, citation.usc_title, citation.usc_section))
                part_of_pair[(citation.usc_title, citation.usc_section)] = part.part
    links_gold = [
        record
        for record in load_typed_jsonl(GOLD_AUTHORITY / "links_gold.jsonl", LinkRecord)
        if isinstance(record, LinkRecord)
    ]
    gold_pairs = {(r.part, r.usc_title, r.usc_section) for r in links_gold}
    tp = len(predicted & gold_pairs)
    fp = len(predicted - gold_pairs)
    fn = len(gold_pairs - predicted)
    link_precision = tp / (tp + fp) if tp + fp else None
    link_recall = tp / (tp + fn) if tp + fn else None
    link_f1 = (
        2 * link_precision * link_recall / (link_precision + link_recall)
        if link_precision and link_recall
        else None
    )
    # Clustered bootstrap by part over the union of pairs.
    link_clusters: dict[int, list[Outcome]] = defaultdict(list)
    for part_number, title, section in predicted | gold_pairs:
        link_clusters[part_number].append(
            (
                (part_number, title, section) in gold_pairs,
                (part_number, title, section) in predicted,
            )
        )
    link_f1_ci = clustered_bootstrap_ci(list(link_clusters.values()), f1_of) if gold_pairs else None
    # Link kappa: agreement between the two frozen enumeration passes on the
    # union of enumerated pairs (present/absent per pass).
    pass1_pairs = {
        (r.part, r.usc_title, r.usc_section)
        for r in load_typed_jsonl(GOLD_AUTHORITY / "links_pass1.jsonl", LinkRecord)
        if isinstance(r, LinkRecord)
    }
    pass2_pairs = {
        (r.part, r.usc_title, r.usc_section)
        for r in load_typed_jsonl(GOLD_AUTHORITY / "links_pass2.jsonl", LinkRecord)
        if isinstance(r, LinkRecord)
    }
    link_kappa: float | None = None
    if pass1_pairs and pass2_pairs:
        union = sorted(pass1_pairs | pass2_pairs)
        link_kappa = cohens_kappa(
            [str(pair in pass1_pairs) for pair in union],
            [str(pair in pass2_pairs) for pair in union],
        )

    # --- Classification accuracy: pipeline vs gold on unique resolved sections.
    pipeline_class: dict[str, str] = {}
    for part in export.parts:
        for resolved in part.resolved:
            pipeline_class[_pair_key(resolved.usc_title, resolved.usc_section)] = (
                resolved.classification.value
            )
    class_gold = [
        record
        for record in load_typed_jsonl(GOLD_AUTHORITY / "class_gold.jsonl", ClassRecord)
        if isinstance(record, ClassRecord)
    ]
    class_outcomes: list[bool] = []
    class_clusters: dict[int, list[bool]] = defaultdict(list)
    for record in class_gold:
        predicted_label = pipeline_class.get(record.pair_id)
        if predicted_label is None:
            continue
        correct = predicted_label == record.classification
        class_outcomes.append(correct)
        cluster = part_of_pair.get((record.usc_title, record.usc_section), 0)
        class_clusters[cluster].append(correct)
    class_n = len(class_outcomes)
    class_correct = sum(class_outcomes)

    def _accuracy_of(items: Sequence[bool]) -> float | None:
        return sum(items) / len(items) if items else None

    class_ci = (
        clustered_bootstrap_ci(list(class_clusters.values()), _accuracy_of)
        if class_outcomes
        else None
    )
    pass1_class = {
        r.pair_id: r.classification
        for r in load_typed_jsonl(GOLD_AUTHORITY / "class_pass1.jsonl", ClassRecord)
        if isinstance(r, ClassRecord)
    }
    pass2_class = {
        r.pair_id: r.classification
        for r in load_typed_jsonl(GOLD_AUTHORITY / "class_pass2.jsonl", ClassRecord)
        if isinstance(r, ClassRecord)
    }
    shared = sorted(pass1_class.keys() & pass2_class.keys())
    class_kappa = (
        cohens_kappa([pass1_class[k] for k in shared], [pass2_class[k] for k in shared])
        if shared
        else None
    )

    # --- Grounding retrieval: precision from in-context judgments; recall vs
    # judged-genuine spans plus independently swept missed occurrences.
    grounding_gold = [
        record
        for record in load_typed_jsonl(GOLD_GROUNDING / "gold.jsonl", MarkerJudgment)
        if isinstance(record, MarkerJudgment)
    ]
    judgments = [r for r in grounding_gold if r.kind == "judgment"]
    missed = [r for r in grounding_gold if r.kind == "missed"]
    genuine = sum(1 for r in judgments if r.genuine)
    marker_precision = genuine / len(judgments) if judgments else None
    marker_recall = genuine / (genuine + len(missed)) if genuine + len(missed) else None
    pass1_g = {
        (r.document_number, r.start, r.end): bool(r.genuine)
        for r in load_typed_jsonl(GOLD_GROUNDING / "pass1.jsonl", MarkerJudgment)
        if isinstance(r, MarkerJudgment) and r.kind == "judgment"
    }
    pass2_g = {
        (r.document_number, r.start, r.end): bool(r.genuine)
        for r in load_typed_jsonl(GOLD_GROUNDING / "pass2.jsonl", MarkerJudgment)
        if isinstance(r, MarkerJudgment) and r.kind == "judgment"
    }
    shared_g = sorted(pass1_g.keys() & pass2_g.keys())
    grounding_kappa = (
        cohens_kappa([str(pass1_g[k]) for k in shared_g], [str(pass2_g[k]) for k in shared_g])
        if shared_g
        else None
    )

    total_sections = export.total_section_citations
    all_gold = [*links_gold, *class_gold, *grounding_gold]
    adjudicated = sum(1 for record in all_gold if record.adjudicated)
    label = (
        f"Provisional — machine-proposed labels, human-adjudicated: "
        f"{adjudicated}/{len(all_gold)}. Metrics will be restated as adjudication proceeds."
        if adjudicated < len(all_gold)
        else f"Human-adjudicated gold set ({adjudicated}/{len(all_gold)})."
    )
    return Ogc01EvalReport(
        link_gold_count=len(gold_pairs),
        link_predicted_count=len(predicted),
        link_tp=tp,
        link_fp=fp,
        link_fn=fn,
        link_precision=link_precision,
        link_recall=link_recall,
        link_f1=link_f1,
        link_precision_wilson=wilson_interval(tp, tp + fp) if tp + fp else None,
        link_recall_wilson=wilson_interval(tp, tp + fn) if tp + fn else None,
        link_f1_bootstrap=(link_f1_ci.low, link_f1_ci.high) if link_f1_ci else None,
        link_kappa=link_kappa,
        class_n=class_n,
        class_correct=class_correct,
        class_accuracy=class_correct / class_n if class_n else None,
        class_accuracy_wilson=wilson_interval(class_correct, class_n) if class_n else None,
        class_accuracy_bootstrap=(class_ci.low, class_ci.high) if class_ci else None,
        class_kappa=class_kappa,
        class_kappa_band=kappa_band(class_kappa) if class_kappa is not None else None,
        unresolved_count=export.total_unresolved,
        unresolved_rate=export.total_unresolved / total_sections if total_sections else 0.0,
        non_section_citations=export.total_non_section_citations,
        authority_gate_rejections=export.gate_rejections,
        marker_judged=len(judgments),
        marker_genuine=genuine,
        marker_precision=marker_precision,
        marker_precision_wilson=(wilson_interval(genuine, len(judgments)) if judgments else None),
        marker_missed=len(missed),
        marker_recall=marker_recall,
        marker_recall_wilson=(
            wilson_interval(genuine, genuine + len(missed)) if genuine + len(missed) else None
        ),
        grounding_kappa=grounding_kappa,
        grounding_gate_rejections=int(grounding["total_gate_rejections"]),
        draft_generated=int(conformance["generated"]),
        draft_accepted=int(conformance["accepted"]),
        draft_pass_rate=float(conformance["pass_rate"]),
        draft_unverified_quotes=int(conformance["total_unverified_quotes"]),
        kappa_note=(
            "All kappa values are agreement between two frozen proposal passes by "
            "different models (claude-fable-5 vs claude-sonnet-5) applying the "
            "written guidelines; human inter-annotator kappa pending adjudication."
        ),
        adjudicated_count=adjudicated,
        total_gold_count=len(all_gold),
        provisional_label=label,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens.eval.ogc01")
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(argv)

    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(report.model_dump_json(indent=2) + "\n")
    print(
        f"ogc01: link F1={report.link_f1} class acc={report.class_accuracy} "
        f"(n={report.class_n}) marker P={report.marker_precision} "
        f"R={report.marker_recall} drafts={report.draft_pass_rate:.2f} "
        f"[{report.provisional_label}]"
    )

    gated = {
        "link_f1": report.link_f1,
        "class_accuracy": report.class_accuracy,
        "marker_precision": report.marker_precision,
        "draft_pass_rate": report.draft_pass_rate,
    }
    if args.update_baseline:
        BASELINE_PATH.write_text(json.dumps(gated, indent=2) + "\n")
        return 0
    if args.gate:
        if report.draft_unverified_quotes > 0:
            # Fail-closed guardrail: a shipped draft with an unverified quote
            # is a defect (target is zero by construction).
            print("GATE FAIL: unverified quotes in accepted drafts")
            return 1
        if not BASELINE_PATH.is_file():
            print("GATE: no committed ogc01 baseline yet (armed on first commit)")
            return 0
        baseline = json.loads(BASELINE_PATH.read_text())
        for key, value in gated.items():
            floor = baseline.get(key)
            if (
                isinstance(floor, float)
                and isinstance(value, float)
                and (value < floor - TOLERANCE)
            ):
                print(f"GATE FAIL: {key} {value:.3f} < baseline {floor:.3f} - {TOLERANCE}")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
