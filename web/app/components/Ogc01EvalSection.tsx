"use client";

import { useEffect } from "react";
import { Alert } from "@trussworks/react-uswds";

import { ci, fmt, type MetricInterval } from "./ui/metric-format";
import { useLazyJson } from "./ui/useLazyJson";

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

interface Ogc01EvalSectionProps {
  active: boolean;
}

export function Ogc01EvalSection({ active }: Ogc01EvalSectionProps) {
  const { state, load } = useLazyJson<Ogc01Report>(
    "/data/ogc01-eval.json",
    {
      requestErrorPrefix: "Request failed with status ",
      fallbackErrorMessage:
        "The OGC-01 evaluation report could not be loaded.",
    },
  );

  useEffect(() => {
    if (active) {
      void load();
    }
  }, [active, load]);

  return (
    <section className="eval-section" aria-labelledby="ogc01-eval-heading">
      <h3 id="ogc01-eval-heading">
        Evaluation — authority, grounding, and drafts (provisional)
      </h3>

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
          <Alert type="warning" headingLevel="h4" slim>
            {state.data.provisional_label}
          </Alert>

          <h4>Authority linking (citation pairs — a census)</h4>
          <ul className="eval-details">
            <li>
              Link precision {fmt(state.data.link_precision)}
              {state.data.link_precision_wilson
                ? ` (95% Wilson ${ci(state.data.link_precision_wilson)})`
                : ""}
              , recall {fmt(state.data.link_recall)}
              {state.data.link_recall_wilson
                ? ` (95% Wilson ${ci(state.data.link_recall_wilson)})`
                : ""}
              , F1 {fmt(state.data.link_f1)}
              {state.data.link_f1_bootstrap
                ? ` (cluster-resampling range ${ci(state.data.link_f1_bootstrap)})`
                : ""}{" "}
              — TP {state.data.link_tp} / FP {state.data.link_fp} / FN{" "}
              {state.data.link_fn} over {state.data.link_gold_count} gold pairs.
            </li>
            <li>
              Classification accuracy over {"{mandatory, discretionary, silent}"}:{" "}
              {fmt(state.data.class_accuracy)} ({state.data.class_correct}/
              {state.data.class_n}
              {state.data.class_accuracy_wilson
                ? `; 95% Wilson ${ci(state.data.class_accuracy_wilson)}`
                : ""}
              {state.data.class_accuracy_bootstrap
                ? `; cluster-resampling range ${ci(state.data.class_accuracy_bootstrap)}`
                : ""}
              {state.data.class_effective_n !== null
                ? `; effective n ≈ ${Math.round(state.data.class_effective_n)}` +
                  (state.data.class_design_effect !== null
                    ? ` (design effect ${state.data.class_design_effect.toFixed(2)})`
                    : "")
                : ""}
              ).
            </li>
            <li>
              Coverage facts (not errors): {state.data.unresolved_count} citations
              unresolved in the pinned USLM release (
              {(state.data.unresolved_rate * 100).toFixed(1)}%),{" "}
              {state.data.non_section_citations} non-section citations (note / Pub. L. /
              E.O.), {state.data.authority_gate_rejections} provenance-gate rejections.
            </li>
            <li>
              Cross-model agreement — pair enumeration:{" "}
              {state.data.link_kappa !== null
                ? `kappa ${state.data.link_kappa.toFixed(2)}`
                : state.data.link_pass_agreement !== null
                  ? `raw agreement ${state.data.link_pass_agreement.toFixed(2)} ` +
                    "(kappa undefined: identical passes leave no negative instances)"
                  : "—"}
              ; classification:{" "}
              {state.data.class_kappa === null
                ? "—"
                : `kappa ${state.data.class_kappa.toFixed(2)} (${
                    state.data.class_kappa_band ?? ""
                  }, Landis-Koch)`}
              .
            </li>
            <li>{state.data.cluster_caveat}</li>
            <li>{state.data.bootstrap_note}</li>
          </ul>

          <h4>Grounding-marker retrieval</h4>
          <ul className="eval-details">
            <li>
              In-context precision {fmt(state.data.marker_precision)} (
              {state.data.marker_genuine}/{state.data.marker_judged} judged genuine
              {state.data.marker_precision_wilson
                ? `; 95% Wilson ${ci(state.data.marker_precision_wilson)}`
                : ""}
              {state.data.marker_precision_bootstrap
                ? `; document-cluster resampling range ${ci(state.data.marker_precision_bootstrap)}`
                : ""}
              ); recall vs the independent sweep {fmt(state.data.marker_recall)} (
              {state.data.marker_missed} missed occurrence
              {state.data.marker_missed === 1 ? "" : "s"}
              {state.data.marker_recall_wilson
                ? `; 95% Wilson ${ci(state.data.marker_recall_wilson)}`
                : ""}
              ).
            </li>
            <li>
              Gate rejection rate: {state.data.grounding_gate_rejections} rejected
              (first-class metric; zero expected by construction).
            </li>
            <li>
              Cross-model kappa on genuineness judgments:{" "}
              {state.data.grounding_kappa === null
                ? "—"
                : `${state.data.grounding_kappa.toFixed(2)} (${
                    state.data.grounding_kappa_band ?? ""
                  }, Landis-Koch)`}
              . {state.data.marker_trust_note}
            </li>
          </ul>

          <h4>Draft skeletons (structural conformance)</h4>
          <ul className="eval-details">
            <li>
              Conformance pass rate {state.data.draft_pass_rate.toFixed(2)} (
              {state.data.draft_accepted}/{state.data.draft_generated} drafts);
              unverified quotes in accepted drafts: {state.data.draft_unverified_quotes}{" "}
              (target 0; a failing draft is rejected, not published).
            </li>
          </ul>

          <p>{state.data.kappa_note}</p>
        </>
      ) : null}
    </section>
  );
}
