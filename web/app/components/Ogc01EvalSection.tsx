"use client";

import { useCallback, useState } from "react";
import { Alert, Button } from "@trussworks/react-uswds";

import { ci, fmt, type MetricInterval } from "./ui/metric-format";

type Ogc01Report = {
  link_gold_count: number;
  link_predicted_count: number;
  link_tp: number;
  link_fp: number;
  link_fn: number;
  link_precision: number | null;
  link_recall: number | null;
  link_f1: number | null;
  link_precision_wilson: MetricInterval | null;
  link_recall_wilson: MetricInterval | null;
  link_f1_bootstrap: MetricInterval | null;
  link_kappa: number | null;
  link_pass_agreement: number | null;
  class_n: number;
  class_correct: number;
  class_accuracy: number | null;
  class_accuracy_wilson: MetricInterval | null;
  class_accuracy_bootstrap: MetricInterval | null;
  class_icc: number | null;
  class_design_effect: number | null;
  class_effective_n: number | null;
  class_kappa: number | null;
  class_kappa_band: string | null;
  unresolved_count: number;
  unresolved_rate: number;
  non_section_citations: number;
  authority_gate_rejections: number;
  marker_judged: number;
  marker_genuine: number;
  marker_precision: number | null;
  marker_precision_wilson: MetricInterval | null;
  marker_precision_bootstrap: MetricInterval | null;
  marker_missed: number;
  marker_missed_pending: number;
  marker_judged_excluded: number;
  marker_recall: number | null;
  marker_recall_wilson: MetricInterval | null;
  grounding_kappa: number | null;
  grounding_kappa_band: string | null;
  marker_trust_note: string;
  grounding_gate_rejections: number;
  draft_generated: number;
  draft_accepted: number;
  draft_pass_rate: number;
  draft_unverified_quotes: number;
  kappa_note: string;
  bootstrap_note: string;
  cluster_caveat: string;
  adjudicated_count: number;
  total_gold_count: number;
  provisional_label: string;
};

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; report: Ogc01Report }
  | { status: "error"; message: string };

export function Ogc01EvalSection() {
  const [state, setState] = useState<State>({ status: "idle" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const response = await fetch("/data/ogc01-eval.json");
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}.`);
      }
      const report = (await response.json()) as Ogc01Report;
      setState({ status: "ready", report });
    } catch (error: unknown) {
      setState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "The OGC-01 evaluation report could not be loaded.",
      });
    }
  }, []);

  return (
    <section className="eval-section" aria-labelledby="ogc01-eval-heading">
      <h2 id="ogc01-eval-heading">
        Evaluation — authority, grounding, and drafts (provisional)
      </h2>

      {state.status === "idle" ? (
        <Button type="button" outline onClick={() => void load()}>
          Load the OGC-01 evaluation metrics
        </Button>
      ) : null}
      {state.status === "loading" ? (
        <p role="status">Loading the OGC-01 evaluation report…</p>
      ) : null}
      {state.status === "error" ? (
        <p role="alert">
          The OGC-01 evaluation report could not be loaded. {state.message}
        </p>
      ) : null}

      {state.status === "ready" ? (
        <>
          <Alert type="warning" headingLevel="h3" slim>
            {state.report.provisional_label}
          </Alert>

          <h3>Authority linking (citation pairs — a census)</h3>
          <ul className="eval-details">
            <li>
              Link precision {fmt(state.report.link_precision)}
              {state.report.link_precision_wilson
                ? ` (95% Wilson ${ci(state.report.link_precision_wilson)})`
                : ""}
              , recall {fmt(state.report.link_recall)}
              {state.report.link_recall_wilson
                ? ` (95% Wilson ${ci(state.report.link_recall_wilson)})`
                : ""}
              , F1 {fmt(state.report.link_f1)}
              {state.report.link_f1_bootstrap
                ? ` (cluster-resampling range ${ci(state.report.link_f1_bootstrap)})`
                : ""}{" "}
              — TP {state.report.link_tp} / FP {state.report.link_fp} / FN{" "}
              {state.report.link_fn} over {state.report.link_gold_count} gold pairs.
            </li>
            <li>
              Classification accuracy over {"{mandatory, discretionary, silent}"}:{" "}
              {fmt(state.report.class_accuracy)} ({state.report.class_correct}/
              {state.report.class_n}
              {state.report.class_accuracy_wilson
                ? `; 95% Wilson ${ci(state.report.class_accuracy_wilson)}`
                : ""}
              {state.report.class_accuracy_bootstrap
                ? `; cluster-resampling range ${ci(state.report.class_accuracy_bootstrap)}`
                : ""}
              {state.report.class_effective_n !== null
                ? `; effective n ≈ ${Math.round(state.report.class_effective_n)}` +
                  (state.report.class_design_effect !== null
                    ? ` (design effect ${state.report.class_design_effect.toFixed(2)})`
                    : "")
                : ""}
              ).
            </li>
            <li>
              Coverage facts (not errors): {state.report.unresolved_count} citations
              unresolved in the pinned USLM release (
              {(state.report.unresolved_rate * 100).toFixed(1)}%),{" "}
              {state.report.non_section_citations} non-section citations (note / Pub. L. /
              E.O.), {state.report.authority_gate_rejections} provenance-gate rejections.
            </li>
            <li>
              Cross-model agreement — pair enumeration:{" "}
              {state.report.link_kappa !== null
                ? `kappa ${state.report.link_kappa.toFixed(2)}`
                : state.report.link_pass_agreement !== null
                  ? `raw agreement ${state.report.link_pass_agreement.toFixed(2)} ` +
                    "(kappa undefined: identical passes leave no negative instances)"
                  : "—"}
              ; classification:{" "}
              {state.report.class_kappa === null
                ? "—"
                : `kappa ${state.report.class_kappa.toFixed(2)} (${
                    state.report.class_kappa_band ?? ""
                  }, Landis-Koch)`}
              .
            </li>
            <li>{state.report.cluster_caveat}</li>
            <li>{state.report.bootstrap_note}</li>
          </ul>

          <h3>Grounding-marker retrieval</h3>
          <ul className="eval-details">
            <li>
              In-context precision {fmt(state.report.marker_precision)} (
              {state.report.marker_genuine}/{state.report.marker_judged} judged genuine
              {state.report.marker_precision_wilson
                ? `; 95% Wilson ${ci(state.report.marker_precision_wilson)}`
                : ""}
              {state.report.marker_precision_bootstrap
                ? `; document-cluster resampling range ${ci(state.report.marker_precision_bootstrap)}`
                : ""}
              ); recall vs the independent sweep {fmt(state.report.marker_recall)} (
              {state.report.marker_missed} missed occurrence
              {state.report.marker_missed === 1 ? "" : "s"}
              {state.report.marker_recall_wilson
                ? `; 95% Wilson ${ci(state.report.marker_recall_wilson)}`
                : ""}
              ).
            </li>
            <li>
              Gate rejection rate: {state.report.grounding_gate_rejections} rejected
              (first-class metric; zero expected by construction).
            </li>
            <li>
              Cross-model kappa on genuineness judgments:{" "}
              {state.report.grounding_kappa === null
                ? "—"
                : `${state.report.grounding_kappa.toFixed(2)} (${
                    state.report.grounding_kappa_band ?? ""
                  }, Landis-Koch)`}
              . {state.report.marker_trust_note}
            </li>
          </ul>

          <h3>Draft skeletons (structural conformance)</h3>
          <ul className="eval-details">
            <li>
              Conformance pass rate {state.report.draft_pass_rate.toFixed(2)} (
              {state.report.draft_accepted}/{state.report.draft_generated} drafts);
              unverified quotes in accepted drafts: {state.report.draft_unverified_quotes}{" "}
              (target 0; a failing draft is rejected, not published).
            </li>
          </ul>

          <p>{state.report.kappa_note}</p>
        </>
      ) : null}
    </section>
  );
}
