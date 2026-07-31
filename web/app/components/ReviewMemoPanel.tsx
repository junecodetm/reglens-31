"use client";

import { useEffect } from "react";

import { BAND_DEFINITION } from "./GroundingSection";
import { useLazyJson } from "./ui/useLazyJson";

type ReviewClassification =
  | "mandatory"
  | "discretionary"
  | "silent"
  | "unresolved";

interface ReviewMemoData {
  review_note: string;
  model_note: string;
  memos: Array<{
    part: number;
    part_heading: string;
    authority_text: string;
    citations: Array<{
      citation: string;
      classification: ReviewClassification;
      verb_quote: string | null;
    }>;
    unresolved_citations: number;
    non_section_citations: number;
    markers: {
      preamble_rules: number;
      deference_count: number;
      grounding_count: number;
      deference_band: string;
      grounding_band: string;
      coverage_note: string | null;
    };
    narrative: string | null;
    narrative_rejected: boolean;
    rejection_reasons: string[];
  }>;
}

interface ReviewMemoPanelProps {
  part: number;
  compact?: boolean;
}

const NEUTRAL_CHIP_CLASS =
  "usa-tag bg-base-lighter text-ink text-normal";
const MARKER_FACT_CLASS =
  "display-flex flex-wrap gap-05 flex-1 bg-base-lightest border border-base-lighter radius-sm padding-1 text-ink";

export function ReviewMemoPanel({
  part,
  compact = false,
}: ReviewMemoPanelProps) {
  const { state: memoState, load: loadMemoData } =
    useLazyJson<ReviewMemoData>("/data/memos.json", {
      requestErrorPrefix: "The review-memo request returned status ",
      fallbackErrorMessage: "The review-memo data could not be loaded.",
    });

  useEffect(() => {
    void loadMemoData();
  }, [loadMemoData, part]);

  if (memoState.status !== "ready") {
    return null;
  }

  const memo = memoState.data.memos.find((item) => item.part === part);

  if (memo === undefined) {
    return null;
  }

  const mandatoryCount = memo.citations.filter(
    (citation) => citation.classification === "mandatory",
  ).length;
  const discretionaryCount = memo.citations.filter(
    (citation) => citation.classification === "discretionary",
  ).length;
  const silentCount = memo.citations.filter(
    (citation) => citation.classification === "silent",
  ).length;
  const Heading = compact ? "h3" : "h2";
  const headingId = `review-memo-${compact ? "compact-" : ""}${part}-heading`;

  return (
    <section
      className="bg-base-lightest border border-base-lighter radius-sm padding-2 margin-y-2 text-ink"
      aria-labelledby={headingId}
    >
      <Heading id={headingId} className="margin-top-0">
        Review signals — flagged for attorney review
      </Heading>

      {!compact ? (
        <div className="neutral-notice margin-y-2" role="note">
          <p>{memoState.data.review_note}</p>
          <p className="margin-top-1">{memoState.data.model_note}</p>
        </div>
      ) : null}

      <p className="margin-y-1">
        <strong>31 CFR Part {memo.part}:</strong> {memo.part_heading}
      </p>

      <ul
        className="add-list-reset display-flex flex-wrap gap-1 margin-y-2"
        aria-label={`Authority classifications for 31 CFR Part ${memo.part}`}
      >
        <li>
          <span className={NEUTRAL_CHIP_CLASS}>
            mandatory {mandatoryCount}
          </span>
        </li>
        <li>
          <span className={NEUTRAL_CHIP_CLASS}>
            discretionary {discretionaryCount}
          </span>
        </li>
        <li>
          <span className={NEUTRAL_CHIP_CLASS}>silent {silentCount}</span>
        </li>
        {memo.unresolved_citations > 0 ? (
          <li>
            <span className={NEUTRAL_CHIP_CLASS}>
              unresolved {memo.unresolved_citations}
            </span>
          </li>
        ) : null}
      </ul>

      <dl
        className="display-flex flex-wrap gap-1 margin-y-2"
        aria-label={`Textual-marker facts for 31 CFR Part ${memo.part}`}
      >
        <div className={MARKER_FACT_CLASS}>
          <dt className="text-bold">Deference-reliance markers:</dt>
          <dd className="margin-0">
            {memo.markers.deference_count} — {memo.markers.deference_band}{" "}
            textual-marker density
          </dd>
        </div>
        <div className={MARKER_FACT_CLASS}>
          <dt className="text-bold">Grounding-strength markers:</dt>
          <dd className="margin-0">
            {memo.markers.grounding_count} — {memo.markers.grounding_band}{" "}
            textual-marker density
          </dd>
        </div>
      </dl>
      <div
        className="bg-base-lightest border-left-05 border-base padding-2 margin-bottom-2"
        role="note"
        aria-label="Textual-marker density definition"
      >
        <p className="margin-y-0">{BAND_DEFINITION}</p>
      </div>

      {memo.markers.coverage_note !== null ? (
        <p className="margin-y-2">{memo.markers.coverage_note}</p>
      ) : null}

      {memo.narrative_rejected ? (
        <div className="neutral-notice margin-y-2" role="note">
          <p>
            <strong>Narrative withheld by the memo gate.</strong>
          </p>
          <ul className="eval-details">
            {memo.rejection_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      ) : memo.narrative !== null ? (
        <div className="margin-y-2">
          <p className="model-generated-note">
            <strong>Model-generated summary of the retrieval evidence — not a legal conclusion.</strong>
          </p>
          <p>{memo.narrative}</p>
        </div>
      ) : null}

      {compact ? (
        <p className="margin-bottom-0">
          <a href="/authorities/">
            Full evidence on the Statutory authority page
          </a>
        </p>
      ) : (
        <>
          <section aria-labelledby={`review-memo-${part}-authority-heading`}>
            <h3 id={`review-memo-${part}-authority-heading`}>
              Authority citation text
            </h3>
            <blockquote className="margin-x-0">
              {memo.authority_text}
            </blockquote>
          </section>

          <dl
            className="display-flex flex-wrap gap-1 margin-y-2"
            aria-label={`Additional review facts for 31 CFR Part ${memo.part}`}
          >
            <div className={MARKER_FACT_CLASS}>
              <dt className="text-bold">Unresolved citations:</dt>
              <dd className="margin-0">{memo.unresolved_citations}</dd>
            </div>
            <div className={MARKER_FACT_CLASS}>
              <dt className="text-bold">Non-section citations:</dt>
              <dd className="margin-0">{memo.non_section_citations}</dd>
            </div>
            <div className={MARKER_FACT_CLASS}>
              <dt className="text-bold">Preamble rules reviewed:</dt>
              <dd className="margin-0">{memo.markers.preamble_rules}</dd>
            </div>
          </dl>

          <details className="draft-checklist-details">
            <summary>Show citation-level evidence</summary>
            <ul
              className="eval-details"
              aria-label={`Citation-level evidence for 31 CFR Part ${memo.part}`}
            >
              {memo.citations.map((citation, index) => (
                <li key={`${citation.citation}-${index}`}>
                  <p className="margin-y-1">
                    <strong>{citation.citation}</strong>{" "}
                    <span className={NEUTRAL_CHIP_CLASS}>
                      {citation.classification}
                    </span>
                  </p>
                  <p className="margin-y-1">
                    <strong>Recorded verb passage:</strong>{" "}
                    {citation.verb_quote === null ? (
                      "None recorded"
                    ) : (
                      <q>{citation.verb_quote}</q>
                    )}
                  </p>
                </li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}
