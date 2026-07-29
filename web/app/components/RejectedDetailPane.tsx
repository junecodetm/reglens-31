"use client";

import {
  type ClaimRecord,
  hasClosestPassage,
  type RejectedDetailsData,
  type SourceTextState,
} from "./reglens-types";
import { DiffComparison } from "./ui/DiffComparison";
import { GlossaryTerm } from "./ui/GlossaryTerm";
import { HighlightedText } from "./ui/HighlightedText";
import type { LazyJsonState } from "./ui/useLazyJson";

export const REJECTION_REASON_EXPLANATIONS: Record<string, string> = {
  "not-a-substring":
    "This exact wording does not appear anywhere in the source document.",
  "empty-quote": "The model returned no quotable text for this claim.",
  "verification-error":
    "The verification check could not run for this claim.",
};

interface RejectedDetailPaneProps {
  selectedClaim: ClaimRecord | null;
  sourceState: SourceTextState;
  detailsState: LazyJsonState<RejectedDetailsData>;
  standalone?: boolean;
}

export function RejectedDetailPane({
  selectedClaim,
  sourceState,
  detailsState,
  standalone = false,
}: RejectedDetailPaneProps) {
  const PaneHeading = standalone ? "h2" : "h3";
  const InternalHeading = standalone ? "h3" : "h4";

  if (selectedClaim === null) {
    return (
      <section
        className="pane source-pane rejected-detail-pane"
        aria-labelledby="rejected-detail-heading"
      >
        <PaneHeading id="rejected-detail-heading">
          Rejection evidence
        </PaneHeading>
        <div className="instruction-card">
          <p>
            Select a rejected claim to see why the{" "}
            <GlossaryTerm term="provenance-gate">
              provenance gate
            </GlossaryTerm>{" "}
            turned it down.
          </p>
        </div>
      </section>
    );
  }

  const rejectionExplanation =
    (selectedClaim.rejection_reason
      ? REJECTION_REASON_EXPLANATIONS[selectedClaim.rejection_reason]
      : undefined) ??
    "This claim did not pass the verbatim-match check.";

  const entry =
    detailsState.status === "ready"
      ? detailsState.data.details[selectedClaim.claim_id]
      : undefined;
  const hasComparison =
    entry !== undefined && hasClosestPassage(entry);
  const isCurrentDocument =
    sourceState.status !== "idle" &&
    sourceState.documentNumber === selectedClaim.document_number;

  return (
    <section
      className="pane source-pane rejected-detail-pane"
      aria-labelledby="rejected-detail-heading"
    >
      <PaneHeading id="rejected-detail-heading">
        Rejection evidence
      </PaneHeading>

      <div className="claim-detail-card">
        <blockquote>
          <span className="screen-reader-only">
            The model&apos;s proposed quote:
          </span>
          {selectedClaim.quote}
        </blockquote>
        <p className="rejection-reason">{rejectionExplanation}</p>
      </div>

      {detailsState.status === "idle" ||
      detailsState.status === "loading" ? (
        <p className="loading-state" role="status">
          Loading the closest-match comparison…
        </p>
      ) : null}

      {detailsState.status === "error" ? (
        <div className="error-state" role="alert">
          <InternalHeading>Comparison unavailable</InternalHeading>
          <p>{detailsState.message}</p>
        </div>
      ) : null}

      {detailsState.status === "ready" && entry === undefined ? (
        <p className="neutral-notice">
          No closest-passage comparison is available for this claim.
        </p>
      ) : null}

      {detailsState.status === "ready" &&
      entry !== undefined &&
      !hasClosestPassage(entry) ? (
        <p className="neutral-notice">
          No passage in the source is similar enough to compare (similarity{" "}
          {Math.round(entry.similarity * 100)}%).
        </p>
      ) : null}

      {hasComparison ? (
        <>
          <InternalHeading>
            Closest passage in the source (automatic comparison)
          </InternalHeading>
          <p>
            The words below that don&apos;t line up are why this claim was
            rejected.
          </p>
          <p
            className="diff-comparison"
            aria-label="Word-level comparison of the model's quote against the closest source passage"
          >
            <DiffComparison diff={entry.diff} />
          </p>

          {!isCurrentDocument || sourceState.status === "loading" ? (
            <p className="loading-state" role="status">
              Loading source document…
            </p>
          ) : null}

          {isCurrentDocument && sourceState.status === "error" ? (
            <div className="error-state" role="alert">
              <InternalHeading>
                Source document unavailable
              </InternalHeading>
              <p>{sourceState.message}</p>
            </div>
          ) : null}

          {isCurrentDocument && sourceState.status === "ready" ? (
            <HighlightedText
              text={sourceState.text}
              start={entry.closest_start}
              end={entry.closest_end}
              selectionKey={`rejected-${selectedClaim.claim_id}`}
              regionLabel="Source document text"
              highlightStatus="Nearest passage in the source shown below — this is a proximity match, not a verified quote."
              noSpanMessage="No closest-passage span is available, so the source is shown without a highlighted passage."
              boundsMessage="The closest-passage span falls outside the source text, so the source is shown without a highlighted passage."
              retryWhenVisible={false}
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}
