"use client";

import { useEffect } from "react";
import { Alert } from "@trussworks/react-uswds";

import { MetricCard } from "./ui/MetricCard";
import { fmt, type MetricInterval } from "./ui/metric-format";
import { useLazyJson } from "./ui/useLazyJson";

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

interface EvalSectionProps {
  active: boolean;
  standalone?: boolean;
}

export function EvalSection({
  active,
  standalone = false,
}: EvalSectionProps) {
  const { state, load } = useLazyJson<EvalReport>("/data/eval.json", {
    requestErrorPrefix: "Request failed with status ",
    fallbackErrorMessage: "The evaluation report could not be loaded.",
  });

  useEffect(() => {
    if (active) {
      void load();
    }
  }, [active, load]);

  const internalHeadingLevel = standalone ? "h2" : "h4";

  return (
    <section
      className="eval-section"
      aria-label={standalone ? "Evaluation — honest, provisional" : undefined}
      aria-labelledby={standalone ? undefined : "eval-heading"}
    >
      {!standalone ? (
        <h3 id="eval-heading">Evaluation — honest, provisional</h3>
      ) : null}

      {state.status === "loading" ? (
        <p role="status">Loading the evaluation report…</p>
      ) : null}

      {state.status === "error" ? (
        <p role="alert">The evaluation report could not be loaded. {state.message}</p>
      ) : null}

      {state.status === "ready" ? (
        <>
          <Alert type="warning" headingLevel={internalHeadingLevel} slim>
            {state.data.provisional_label}
          </Alert>

          <div className="metric-grid">
            <MetricCard
              headingLevel={internalHeadingLevel}
              label="Precision"
              value={state.data.precision}
              intervals={[
                {
                  label: "95% Wilson",
                  interval: state.data.precision_wilson,
                },
                {
                  label: "95% clustered bootstrap",
                  interval: state.data.precision_bootstrap,
                },
              ]}
            />
            <MetricCard
              headingLevel={internalHeadingLevel}
              label="Recall"
              value={state.data.recall}
              intervals={[
                {
                  label: "95% Wilson",
                  interval: state.data.recall_wilson,
                },
                {
                  label: "95% clustered bootstrap",
                  interval: state.data.recall_bootstrap,
                },
              ]}
            />
            <MetricCard
              headingLevel={internalHeadingLevel}
              label="F1"
              value={state.data.f1}
              intervals={[
                {
                  label: "95% clustered bootstrap",
                  interval: state.data.f1_bootstrap,
                },
              ]}
            />
          </div>

          <ul className="eval-details">
            <li>
              Citation fidelity: {fmt(state.data.citation_fidelity)} (guardrail — 1.0 by
              construction of the fail-closed gate)
            </li>
            <li>
              Cohen&apos;s kappa:{" "}
              {state.data.kappa_pass1_pass2 === null
                ? "pending adjudication"
                : `${state.data.kappa_pass1_pass2.toFixed(2)} (${state.data.kappa_band ?? ""}, Landis-Koch)`}{" "}
              — {state.data.kappa_note}
            </li>
            <li>
              n = {state.data.n_provisions} provisions across {state.data.n_documents}{" "}
              documents; effective n ≈ {Math.round(state.data.effective_n)} for the{" "}
              {state.data.icc_outcome} (design effect {state.data.design_effect.toFixed(2)},
              ICC {state.data.icc.toFixed(2)})
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
