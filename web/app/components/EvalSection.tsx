"use client";

import { useEffect, useState } from "react";
import { Alert } from "@trussworks/react-uswds";

import { MetricCard } from "./ui/MetricCard";
import { fmt, type MetricInterval } from "./ui/metric-format";

type EvalReport = {
  n_provisions: number;
  n_documents: number;
  precision: number;
  recall: number;
  f1: number;
  precision_wilson: MetricInterval;
  recall_wilson: MetricInterval;
  precision_bootstrap: MetricInterval;
  recall_bootstrap: MetricInterval;
  f1_bootstrap: MetricInterval;
  kappa_pass1_pass2: number | null;
  kappa_band: string | null;
  kappa_note: string;
  citation_fidelity: number;
  icc: number;
  icc_outcome: string;
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
              intervals={[
                {
                  label: "95% Wilson",
                  interval: state.report.precision_wilson,
                },
                {
                  label: "95% clustered bootstrap",
                  interval: state.report.precision_bootstrap,
                },
              ]}
            />
            <MetricCard
              label="Recall"
              value={state.report.recall}
              intervals={[
                {
                  label: "95% Wilson",
                  interval: state.report.recall_wilson,
                },
                {
                  label: "95% clustered bootstrap",
                  interval: state.report.recall_bootstrap,
                },
              ]}
            />
            <MetricCard
              label="F1"
              value={state.report.f1}
              intervals={[
                {
                  label: "95% clustered bootstrap",
                  interval: state.report.f1_bootstrap,
                },
              ]}
            />
          </div>

          <ul className="eval-details">
            <li>
              Citation fidelity: {fmt(state.report.citation_fidelity)} (guardrail — 1.0 by
              construction of the fail-closed gate)
            </li>
            <li>
              Cohen&apos;s kappa:{" "}
              {state.report.kappa_pass1_pass2 === null
                ? "pending adjudication"
                : `${state.report.kappa_pass1_pass2.toFixed(2)} (${state.report.kappa_band ?? ""}, Landis-Koch)`}{" "}
              — {state.report.kappa_note}
            </li>
            <li>
              n = {state.report.n_provisions} provisions across {state.report.n_documents}{" "}
              documents; effective n ≈ {Math.round(state.report.effective_n)} for the{" "}
              {state.report.icc_outcome} (design effect {state.report.design_effect.toFixed(2)},
              ICC {state.report.icc.toFixed(2)})
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
