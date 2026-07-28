"use client";

import { useEffect, useState } from "react";
import { Alert } from "@trussworks/react-uswds";

type Interval = [number, number];

type EvalReport = {
  n_provisions: number;
  n_documents: number;
  precision: number;
  recall: number;
  f1: number;
  precision_wilson: Interval;
  recall_wilson: Interval;
  precision_bootstrap: Interval;
  recall_bootstrap: Interval;
  f1_bootstrap: Interval;
  kappa_pass1_pass2: number | null;
  citation_fidelity: number;
  icc: number;
  design_effect: number;
  effective_n: number;
  adjudicated_count: number;
  total_gold_count: number;
  provisional_label: string;
};

type EvalState =
  | { status: "loading" }
  | { status: "ready"; report: EvalReport }
  | { status: "error"; message: string };

function fmt(value: number): string {
  return value.toFixed(3);
}

function ci(interval: Interval): string {
  return `[${fmt(interval[0])}, ${fmt(interval[1])}]`;
}

function MetricCard({
  label,
  value,
  wilson,
  bootstrap,
}: {
  label: string;
  value: number;
  wilson?: Interval;
  bootstrap: Interval;
}) {
  return (
    <div className="metric-card">
      <h3>{label}</h3>
      <p className="metric-value">{fmt(value)}</p>
      {wilson ? <p className="metric-ci">95% Wilson {ci(wilson)}</p> : null}
      <p className="metric-ci">95% clustered bootstrap {ci(bootstrap)}</p>
    </div>
  );
}

export function EvalSection() {
  const [state, setState] = useState<EvalState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch("/data/eval.json", {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}.`);
        }
        const report = (await response.json()) as EvalReport;
        if (!controller.signal.aborted) {
          setState({ status: "ready", report });
        }
      } catch (error: unknown) {
        if (!controller.signal.aborted) {
          setState({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "The evaluation report could not be loaded.",
          });
        }
      }
    }

    void load();
    return () => controller.abort();
  }, []);

  return (
    <section className="eval-section" aria-labelledby="eval-heading">
      <h2 id="eval-heading">Evaluation — honest, provisional</h2>

      {state.status === "loading" ? (
        <p role="status">Loading the evaluation report…</p>
      ) : null}

      {state.status === "error" ? (
        <p role="alert">The evaluation report could not be loaded. {state.message}</p>
      ) : null}

      {state.status === "ready" ? (
        <>
          <Alert type="warning" headingLevel="h3" slim>
            {state.report.provisional_label}
          </Alert>

          <div className="metric-grid">
            <MetricCard
              label="Precision"
              value={state.report.precision}
              wilson={state.report.precision_wilson}
              bootstrap={state.report.precision_bootstrap}
            />
            <MetricCard
              label="Recall"
              value={state.report.recall}
              wilson={state.report.recall_wilson}
              bootstrap={state.report.recall_bootstrap}
            />
            <MetricCard
              label="F1"
              value={state.report.f1}
              bootstrap={state.report.f1_bootstrap}
            />
          </div>

          <ul className="eval-details">
            <li>
              Citation fidelity: {fmt(state.report.citation_fidelity)} (guardrail — 1.0 by
              construction of the fail-closed gate)
            </li>
            <li>
              Cohen&apos;s kappa (two independent model annotation passes):{" "}
              {state.report.kappa_pass1_pass2 === null
                ? "pending adjudication"
                : state.report.kappa_pass1_pass2.toFixed(2)}{" "}
              — human inter-annotator kappa pending adjudication
            </li>
            <li>
              n = {state.report.n_provisions} provisions across {state.report.n_documents}{" "}
              documents; effective n ≈ {Math.round(state.report.effective_n)} (design effect{" "}
              {state.report.design_effect.toFixed(2)}, ICC {state.report.icc.toFixed(2)})
            </li>
          </ul>

          <p>
            Gold labels are machine-proposed and individually human-adjudicated over time; the
            adjudicated count above updates from the versioned gold set. Metrics are computed
            offline from committed fixtures — no API calls.
          </p>
        </>
      ) : null}
    </section>
  );
}
