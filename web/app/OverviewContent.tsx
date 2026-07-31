"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

import { AboutSection } from "./components/AboutSection";
import { CorpusScope } from "./components/CorpusScope";
import { LegacyHashRedirect } from "./components/shell/LegacyHashRedirect";
import { recordRouteMount } from "./components/shell/route-mount-state";
import {
  type ExampleData,
  hasClosestPassage,
  type SiteData,
} from "./components/reglens-types";
import { DiffComparison } from "./components/ui/DiffComparison";
import { HighlightedText } from "./components/ui/HighlightedText";
import { useLazyJson } from "./components/ui/useLazyJson";
import { DUR, EASE, STAGGER } from "./motion/tokens.ts";
import { useCountUp } from "./motion/useCountUp.ts";

gsap.registerPlugin(useGSAP);

interface TaskCard {
  title: string;
  href: string;
  description: string;
}

const MODULE_CARDS: readonly TaskCard[] = [
  {
    title: "Extracted obligations",
    href: "/obligations",
    description:
      "Extracted obligations organized by document, each linked to its verbatim source sentence, with every rejected claim displayed as evidence.",
  },
  {
    title: "Statutory authority",
    href: "/authorities",
    description:
      "Each regulation's cited statutory authority resolved into the U.S. Code and classified, with two families of preamble markers presented at equal weight.",
  },
  {
    title: "Draft rule skeletons",
    href: "/drafts",
    description:
      "Document Drafting Handbook–structured skeletons for every in-scope part and rule type, each checked by a fail-closed conformance gate.",
  },
  {
    title: "Evaluation",
    href: "/evaluation",
    description:
      "Extractor accuracy measured on a labeled sample and reported with confidence intervals; labels are machine-proposed and marked provisional.",
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
      "A pre-computed static export: every page renders without a live service, and the one optional live call — draft narrative generation — falls back to the committed drafts.",
  },
];

export function OverviewContent() {
  const { state, load } = useLazyJson<SiteData>("/data/site.json");
  const { state: exampleState, load: loadExample } =
    useLazyJson<ExampleData>("/data/example.json");
  const scopeRef = useRef<HTMLDivElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const acceptedCountRef = useRef<HTMLElement>(null);
  const rejectedCountRef = useRef<HTMLElement>(null);

  useEffect(() => {
    // Same focus contract as PageHeader: announce the page on client-side
    // navigation, while preserving an explicit cross-route About anchor.
    const hasMountedRouteBefore = recordRouteMount();

    if (window.location.hash === "#about") {
      document.getElementById("about")?.focus();
    } else if (hasMountedRouteBefore) {
      headingRef.current?.focus();
    }
    void load();
    void loadExample();
  }, [load, loadExample]);

  const site = state.status === "ready" ? state.data : null;
  const example =
    exampleState.status === "ready" ? exampleState.data : null;

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
            <h1 ref={headingRef} tabIndex={-1}>
              RegLens-31
            </h1>
            <p>
              RegLens-31 reads published Treasury regulations and extracts the
              specific obligations they impose — who must do what. Every extracted
              claim is checked against the government&apos;s published text; a claim
              that fails the check is rejected, counted, and shown with the
              comparison.
            </p>
            <p>
              The tool is an independent demonstration of one documented Treasury AI
              use case — OGC-01, the &ldquo;Regulatory Reform Tool&rdquo; — built
              entirely from public sources. See{" "}
              <Link href="#about">About this demonstration</Link> for the
              source record.
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

      <CorpusScope />

      <section
        className="overview-section overview-example"
        aria-labelledby="overview-example"
        data-reveal
      >
        <h2 id="overview-example">
          See it work: one accepted claim, one rejected claim
        </h2>
        <p>The totals above are computed from extractions such as these two.</p>

        {exampleState.status === "loading" ||
        exampleState.status === "idle" ? (
          <p className="loading-state" role="status">
            Loading example…
          </p>
        ) : null}

        {exampleState.status === "error" ? (
          <p className="neutral-notice" role="alert">
            The example could not be loaded. {exampleState.message}
          </p>
        ) : null}

        {example !== null ? (
          <div className="overview-example-grid">
            <article
              className="overview-example-card"
              aria-label="An accepted claim"
            >
              <p className="overview-example-label">
                Accepted — the quoted text appears verbatim in the source
              </p>
              <p className="overview-example-summary">
                {example.accepted.summary}
              </p>
              <p className="overview-example-caption">
                {"Excerpt — the highlighted span is shown with surrounding context from the source document."}
              </p>
              <HighlightedText
                text={example.accepted.excerpt}
                start={example.accepted.span_start}
                end={example.accepted.span_end}
                selectionKey={`example-${example.accepted.claim_id}`}
                regionLabel="Source excerpt"
                highlightStatus="The verified quote is highlighted in the source excerpt."
                noSpanMessage="No span is recorded for this example."
                boundsMessage="The example span does not match the excerpt."
                retryWhenVisible={false}
                showStatus={false}
                scroll="center"
                scrollBehavior="auto"
              />
              <p>
                <Link href="/obligations">
                  See more accepted claims like this
                </Link>
              </p>
            </article>

            <article
              className="overview-example-card"
              aria-label="A rejected claim"
            >
              <p className="overview-example-label">
                Rejected — the quoted text does not appear in the source; the
                comparison shows the difference
              </p>
              <p className="overview-example-summary">
                {example.rejected.summary}
              </p>
              {hasClosestPassage(example.rejected) ? (
                <div
                  className="diff-comparison source-document"
                  tabIndex={0}
                  role="region"
                  aria-label="Rejected quote compared with the closest source passage"
                >
                  <DiffComparison diff={example.rejected.diff} />
                </div>
              ) : null}
              <p>
                <Link href="/obligations#rejected">
                  See more rejected claims like this
                </Link>
              </p>
            </article>
          </div>
        ) : null}
      </section>

      <section
        className="overview-section"
        aria-labelledby="overview-modules"
      >
        <h2 id="overview-modules">What this demonstrates</h2>
        <ul className="overview-cards">
          {MODULE_CARDS.map((card) => (
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
        <p className="overview-quiet-links">
          Also on this site:{" "}
          <Link href="/sources">Search &amp; browse the corpus</Link> and{" "}
          <Link href="#about">About &amp; provenance</Link>.
        </p>
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
              <strong>{step.name}.</strong> {step.detail}
            </li>
          ))}
        </ol>
      </section>

      <AboutSection />
    </div>
  );
}
