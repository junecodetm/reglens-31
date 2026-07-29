"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

import { LegacyHashRedirect } from "./components/shell/LegacyHashRedirect";
import { recordRouteMount } from "./components/shell/route-mount-state";
import { type SiteData } from "./components/reglens-types";
import { useLazyJson } from "./components/ui/useLazyJson";
import { DUR, EASE, STAGGER } from "./motion/tokens";
import { useCountUp } from "./motion/useCountUp";

gsap.registerPlugin(useGSAP);

interface TaskCard {
  title: string;
  href: string;
  description: string;
}

const TASK_CARDS: readonly TaskCard[] = [
  {
    title: "Verify claims against sources",
    href: "/extraction/claims",
    description:
      "Extracted obligations side by side with their primary sources — selecting a claim highlights its verbatim span.",
  },
  {
    title: "Review rejected claims",
    href: "/extraction/rejected",
    description:
      "The claims the fail-closed provenance gate discarded — counted and listed, not hidden.",
  },
  {
    title: "Search the corpus",
    href: "/explore/search",
    description:
      "Lexical search over extracted obligations, U.S. Code sections, CFR part sections, and draft skeletons.",
  },
  {
    title: "Browse Title 31",
    href: "/explore/browse",
    description:
      "Part-to-section navigation over the five ingested parts of 31 CFR, as of the pinned snapshot date.",
  },
  {
    title: "Trace authority cross-references",
    href: "/explore/cross-references",
    description:
      "Which U.S. Code sections each ingested CFR part cites as rulemaking authority, and which are shared across parts.",
  },
  {
    title: "Inspect authority citations",
    href: "/ogc01/authority",
    description:
      "Citations resolved against a pinned U.S. Code release and classified mandatory / discretionary / silent / unresolved from verbatim-verified verb spans.",
  },
  {
    title: "Scan grounding markers",
    href: "/ogc01/grounding",
    description:
      "Two-sided textual markers in published rule preambles, presented with equal weight; counts describe the text, nothing is concluded.",
  },
  {
    title: "Read draft skeletons",
    href: "/ogc01/drafts",
    description:
      "Document Drafting Handbook structure with fail-closed conformance checks; the model writes only two labeled narrative fields.",
  },
  {
    title: "Evaluation — core metrics",
    href: "/evaluation",
    description:
      "Precision, recall, and F1 with Wilson and clustered-bootstrap intervals; labels are machine-proposed and marked provisional.",
  },
  {
    title: "Evaluation — OGC-01 modules",
    href: "/evaluation/ogc01",
    description:
      "Link precision, marker retrieval, and conformance checks for the three OGC-01 demonstration modules.",
  },
];

const PIPELINE_STEPS: readonly { name: string; detail: string }[] = [
  {
    name: "Snapshot",
    detail:
      "Public sources fetched once and stored content-addressed (SHA-256); everything downstream is reproducible from the snapshots.",
  },
  {
    name: "Extract",
    detail: "A local model at temperature 0, JSON-schema constrained.",
  },
  {
    name: "Verify",
    detail:
      "The provenance gate keeps a claim only if its quote is an exact substring of the source; failures are rejected and counted.",
  },
  {
    name: "Store & evaluate",
    detail:
      "SQLite/Parquet artifacts; metrics reported with confidence intervals and provisional labels.",
  },
  {
    name: "Publish",
    detail:
      "A pre-computed static export — the deployed site never calls a backend, a model, or an API key.",
  },
];

export function OverviewContent() {
  const { state, load } = useLazyJson<SiteData>("/data/site.json");
  const scopeRef = useRef<HTMLDivElement>(null);
  const acceptedCountRef = useRef<HTMLElement>(null);
  const rejectedCountRef = useRef<HTMLElement>(null);

  useEffect(() => {
    recordRouteMount();
    load();
  }, [load]);

  const site = state.status === "ready" ? state.data : null;

  useCountUp(acceptedCountRef, site?.accepted_count ?? null);
  useCountUp(rejectedCountRef, site?.rejected_count ?? null);

  useGSAP(
    () => {
      const media = gsap.matchMedia();

      media.add("(prefers-reduced-motion: no-preference)", () => {
        // opacity, not autoAlpha: the staggered cards are links and must
        // stay focusable throughout the reveal.
        gsap.from("[data-reveal]", {
          y: 12,
          opacity: 0,
          duration: DUR.base,
          ease: EASE,
          stagger: STAGGER,
          clearProps: "all",
        });
      });

      return () => media.revert();
    },
    { scope: scopeRef },
  );

  return (
    <div ref={scopeRef}>
      <LegacyHashRedirect />

      <header className="site-header">
        <div className="content-bound header-content">
          <div className="title-block">
            <h1>RegLens-31</h1>
            <p>
              Provenance-gated regulatory obligation extraction — every claim
              verified verbatim against its primary source, fail-closed.
            </p>
            <p>
              An independent working mockup aligned to U.S. Treasury AI use
              case OGC-01 (“Regulatory Reform Tool,” Treasury public AI Use
              Case Inventory) — see{" "}
              <Link href="/about">About this demonstration</Link>.
            </p>
          </div>

          <dl className="header-stats" aria-label="Snapshot totals">
            <div className="stat-badge stat-badge-accepted">
              <dt className="screen-reader-only">Accepted claims</dt>
              <dd>
                <strong data-stat-count ref={acceptedCountRef}>
                  {site?.accepted_count ?? "—"}
                </strong>{" "}
                obligations verified
              </dd>
            </div>
            <div className="stat-badge stat-badge-rejected">
              <dt className="screen-reader-only">Rejected claims</dt>
              <dd>
                <strong data-stat-count ref={rejectedCountRef}>
                  {site?.rejected_count ?? "—"}
                </strong>{" "}
                claims rejected by the provenance gate
              </dd>
            </div>
          </dl>
        </div>
      </header>

      <section
        className="overview-section"
        aria-labelledby="overview-framing"
        data-reveal
      >
        <h2 id="overview-framing">What this demonstrates</h2>
        <p>
          Every claim this site shows survived a deterministic, fail-closed
          provenance check: the extracted text must match its primary source
          verbatim, or it is rejected and counted. The site is a working
          mockup of OGC-01 — the “Regulatory Reform Tool” listed by
          Treasury’s Office of the General Counsel in the public AI Use Case
          Inventory — built from public primary sources only. Where the
          inventory describes OGC-01 in deregulatory terms, this
          demonstration implements deliberately neutral analogs: it makes no
          deregulatory recommendations, nominates no rules or statutes for
          change, and draws no legal conclusions.
        </p>
        <p>
          The verbatim inventory record, its provenance (source URL, fetch
          date, SHA-256), and the mapping from each stated OGC-01 output to
          the module demonstrating it are on{" "}
          <Link href="/about">About this demonstration</Link>.
        </p>
      </section>

      <section className="overview-section" aria-labelledby="overview-tasks">
        <h2 id="overview-tasks">Start with a task</h2>
        <ul className="overview-cards">
          {TASK_CARDS.map((card) => (
            <li key={card.href} data-reveal>
              <Link className="overview-card" href={card.href}>
                <span className="overview-card-title">{card.title}</span>
                <span className="overview-card-description">
                  {card.description}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section
        className="overview-section"
        aria-labelledby="overview-pipeline"
        data-reveal
      >
        <h2 id="overview-pipeline">How the pipeline works</h2>
        <ol className="pipeline-strip">
          {PIPELINE_STEPS.map((step) => (
            <li key={step.name}>
              <strong>{step.name}</strong> — {step.detail}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
