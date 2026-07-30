"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button, Table } from "@trussworks/react-uswds";

import { useLazyJson } from "./ui/useLazyJson";

interface HighImpactUseCase {
  use_case_id: string;
  name: string;
  bureau: string;
}

interface UseCaseInventory {
  schema_version: number;
  source_url: string;
  fetched_at: string;
  sha256: string;
  row: Record<string, string>;
  context: {
    total_use_cases: number;
    high_impact: HighImpactUseCase[];
    general_counsel_use_case_ids: string[];
  };
}

// Exact column headers from the snapshotted CSV (quoted verbatim as labels,
// with runs of whitespace collapsed for display only).
const DISPLAY_FIELDS: readonly string[] = [
  "Use Case ID",
  "Use Case Name",
  "Bureau/Component",
  "Stage of Development",
  "Is the AI use case high-impact?",
  "Use Case Topic Area",
  "AI Classification",
  "What problem is the AI intended to solve?",
  "Describe the AI system’s outputs.",
  "Does this AI use case  involve personally  identifiable information (PII)  that is maintained by the  agency?",
  "Does this project include  custom-developed code?",
];

function displayLabel(header: string): string {
  return header.replace(/\s+/g, " ").trim();
}

const TRACEABILITY: readonly {
  quote: string;
  module: string;
  href: string;
  detail: string;
  linkText: string;
}[] = [
  {
    quote: "“generates draft proposed and final rules”",
    module: "Draft rule skeletons",
    href: "/drafts",
    detail:
      "Deterministic Document Drafting Handbook structure with a fail-closed conformance gate: the model writes only two labeled narrative fields, and any set-out regulatory text must verify verbatim against the source or the draft is rejected.",
    linkText: "Open: Draft rule skeletons",
  },
  {
    quote:
      "“reviews statutes for potential deregulatory actions” / “identify statutes that are not statutorily required …”",
    module: "Statutory authority citations",
    href: "/authorities",
    detail:
      "Every rulemaking authority the ingested CFR parts cite, resolved against a pinned U.S. Code release and classified mandatory / discretionary / silent / unresolved from verbatim-verified verb spans. The classification describes the statutory text; no candidate list and no recommendation is produced.",
    linkText: "Open: Statutory authority citations",
  },
  {
    quote: "“… that are inconsistent with Looper Bright [sic]”",
    module: "Grounding markers",
    href: "/authorities#markers",
    detail:
      "Two-sided retrieval of literal textual markers in published rule preambles — deference-reliance markers and grounding-strength markers, presented with equal weight. Marker counts describe the published text; nothing is ranked, predicted, or concluded.",
    linkText: "Open: Grounding markers",
  },
];

export function AboutSection() {
  const { state, load } = useLazyJson<UseCaseInventory>(
    "/data/use-case-inventory.json",
  );
  const TraceabilityHeading = "h3";

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section
      className="about-section overview-section"
      aria-labelledby="about"
    >
      <h2 id="about" tabIndex={-1}>
        About this demonstration
      </h2>
      <p>
        What OGC-01 is, why this demonstration mocks it up, and exactly which
        stated output each page implements — quoted verbatim from Treasury's
        own public record.
      </p>
      <p>
        RegLens-31 is an independent working mockup of a single publicly
        documented Treasury AI use case: <strong>OGC-01, the “Regulatory
        Reform Tool”</strong> listed by the Office of the General Counsel in
        the U.S. Department of the Treasury’s public AI Use Case Inventory.
        That inventory entry is the only public description of OGC-01. This
        site demonstrates — from public primary sources only — what each of
        its stated outputs can look like when every claim must survive a
        verbatim, fail-closed provenance check.
      </p>
      <p>
        This site is a mockup, not the OGC-01 system: it has no connection to
        it, uses no Treasury-internal information, and is not affiliated
        with, endorsed by, or representing the U.S. Department of the
        Treasury (31 U.S.C. § 333). Where the inventory describes OGC-01 in
        deregulatory terms, this demonstration implements deliberately
        neutral analogs — it makes no deregulatory recommendations, nominates
        no rules or statutes for change, and draws no legal conclusions.
      </p>

      {state.status === "loading" || state.status === "idle" ? (
        <p className="about-inventory-loading">Loading the inventory record…</p>
      ) : state.status === "error" ? (
        <>
          <p className="neutral-notice" role="alert">
            The inventory record could not be loaded. {state.message}
          </p>
          <Button type="button" outline onClick={load}>
            Retry loading the inventory record
          </Button>
        </>
      ) : (
        <>
          <h3 className="about-inventory-context-heading">
            Why this use case
          </h3>
          <p>
            Of the{" "}
            {state.data.context.total_use_cases} use cases in the inventory,
            OGC-01 is the only General Counsel entry and one of{" "}
            {state.data.context.high_impact.length} that Treasury designates
            high-impact (the others are IRS systems). It is listed as
            Pre-Deployment, so no public version of it exists; and its stated
            outputs are all buildable and testable against public regulatory
            data. High impact, no public artifact, verifiable subject matter —
            that combination is why this demonstration mocks up OGC-01 rather
            than any other inventory entry.
          </p>
          <h4 id="about-inventory-heading">
            Treasury’s inventory entry for OGC-01 (selected fields, quoted
            verbatim)
          </h4>
          <Table
            compact
            fullWidth
            aria-labelledby="about-inventory-heading"
          >
            <thead>
              <tr>
                <th scope="col">Inventory field</th>
                <th scope="col">Verbatim value</th>
              </tr>
            </thead>
            <tbody>
              {DISPLAY_FIELDS.filter(
                (field) => state.data.row[field] !== undefined,
              ).map((field) => (
                <tr key={field}>
                  <th scope="row">{displayLabel(field)}</th>
                  <td>{`“${state.data.row[field].trim()}”`}</td>
                </tr>
              ))}
            </tbody>
          </Table>
          <p className="neutral-notice">
            “Looper Bright” is reproduced verbatim from the source file [sic];
            the case referenced is <cite>Loper Bright Enterprises v.
            Raimondo</cite> (2024).
          </p>
          <p>
            Source:{" "}
            <a href={state.data.source_url} rel="noreferrer">
              Treasury AI Use Case Inventory (CSV), home.treasury.gov
            </a>{" "}
            — a U.S. Government work · fetched{" "}
            {state.data.fetched_at.slice(0, 10)}.
          </p>
          <p>
            <strong>Snapshot SHA-256</strong>
            <code className="about-inventory-digest">
              {state.data.sha256}
            </code>
          </p>
          <p>
            Selected fields shown; the complete verbatim row ships in{" "}
            <a href="/data/use-case-inventory.json">use-case-inventory.json</a>
            .
          </p>
        </>
      )}

      <TraceabilityHeading className="about-traceability-heading">
        Stated outputs and what this site demonstrates
      </TraceabilityHeading>
      <p>
        Each output and stated purpose the inventory records for OGC-01, and
        the on-page module demonstrating its neutral equivalent:
      </p>
      <dl className="about-traceability">
        {TRACEABILITY.map((entry) => (
          <div key={entry.module}>
            <dt>{entry.quote}</dt>
            <dd>
              <strong>{entry.module}</strong> — {entry.detail}{" "}
              <Link href={entry.href}>{entry.linkText}</Link>
            </dd>
          </div>
        ))}
      </dl>

      <section
        className="about-governance-docs"
        aria-labelledby="about-governance-docs-heading"
      >
        <h3 id="about-governance-docs-heading">
          Methodology &amp; governance documents
        </h3>
        <p>
          The repository carries the full written record behind this
          demonstration:
        </p>
        <ul>
          <li>
            <a href="https://github.com/junecodetm/reglens-31#readme">
              README — setup, approach, tools, and assumptions
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
          <li>
            <a href="https://github.com/junecodetm/reglens-31/blob/main/docs/M25-21-CROSSWALK.md">
              OMB M-25-21 minimum-practices crosswalk (with NIST AI 600-1
              mappings)
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
          <li>
            <a href="https://github.com/junecodetm/reglens-31/tree/main/governance">
              Model card, data card, AI impact assessment, monitoring &amp;
              rollback plans
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
          <li>
            <a href="https://github.com/junecodetm/reglens-31/blob/main/docs/EVALUATION.md">
              Evaluation methodology — gold set, annotation protocol,
              intervals
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
        </ul>
      </section>
    </section>
  );
}
