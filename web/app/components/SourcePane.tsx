"use client";

import type { ClaimRecord, SourceTextState } from "./reglens-types";
import {
  computeHighlightSegments,
  HighlightedText,
} from "./ui/HighlightedText";

interface SourcePaneProps {
  selectedClaim: ClaimRecord | null;
  sourceState: SourceTextState;
  standalone?: boolean;
}

export function SourcePane({
  selectedClaim,
  sourceState,
  standalone = false,
}: SourcePaneProps) {
  const isCurrentDocument =
    selectedClaim !== null &&
    sourceState.status !== "idle" &&
    sourceState.documentNumber === selectedClaim.document_number;
  const readyText =
    isCurrentDocument && sourceState.status === "ready"
      ? sourceState.text
      : null;
  const highlightResult =
    selectedClaim && readyText
      ? computeHighlightSegments(
          readyText,
          selectedClaim.start,
          selectedClaim.end,
        )
      : null;
  const PaneHeading = standalone ? "h2" : "h3";
  const InternalHeading = standalone ? "h3" : "h4";

  return (
    <section
      className="pane source-pane"
      aria-labelledby="source-heading"
      tabIndex={-1}
    >
      <PaneHeading id="source-heading">Primary source</PaneHeading>

      {!selectedClaim ? (
        <div className="instruction-card">
          <p>
            Select an extracted obligation to inspect its verified quote and
            highlighted span in the primary source.
          </p>
        </div>
      ) : (
        <>
          <div className="claim-detail-card">
            <blockquote>{selectedClaim.quote}</blockquote>
            <dl className="claim-details">
              <div>
                <dt>Obligation type</dt>
                <dd>{selectedClaim.obligation_type}</dd>
              </div>
              <div>
                <dt>Affected party</dt>
                <dd>{selectedClaim.affected_party}</dd>
              </div>
              <div>
                <dt>Effective date</dt>
                <dd>
                  {selectedClaim.effective_date ? (
                    <time dateTime={selectedClaim.effective_date}>
                      {selectedClaim.effective_date}
                    </time>
                  ) : (
                    "Not specified"
                  )}
                </dd>
              </div>
            </dl>
            <p className="model-generated-note">
              Type, party, date, and summary are model-generated; only the quote
              above is provenance-verified against the source.
            </p>
            <a
              href={selectedClaim.document_url}
              className="primary-source-link"
            >
              View on federalregister.gov
              <span aria-hidden="true"> ↗</span>
            </a>
          </div>

          {!isCurrentDocument || sourceState.status === "loading" ? (
            <p className="loading-state" role="status">
              Loading source document…
            </p>
          ) : null}

          {isCurrentDocument && sourceState.status === "error" ? (
            <div className="error-state" role="alert">
              <InternalHeading>Source document unavailable</InternalHeading>
              <p>{sourceState.message}</p>
            </div>
          ) : null}

          {readyText !== null ? (
            <>
              {highlightResult?.status !== "ready" ? (
                <div className="error-state" role="alert">
                  <InternalHeading>Verified span unavailable</InternalHeading>
                  <p>
                    The saved offsets do not match the quoted source text, so
                    no passage has been highlighted.
                  </p>
                </div>
              ) : (
                <p className="screen-reader-only" role="status">
                  Source passage highlighted for {selectedClaim.summary}
                </p>
              )}

              <HighlightedText
                text={readyText}
                start={selectedClaim.start}
                end={selectedClaim.end}
                selectionKey={selectedClaim.claim_id}
                regionLabel="Source document text"
                highlightStatus={`Source passage highlighted for ${selectedClaim.summary}`}
                noSpanMessage="The saved offsets do not match the quoted source text, so no passage has been highlighted."
                boundsMessage="The saved offsets do not match the quoted source text, so no passage has been highlighted."
                retryWhenVisible={false}
                showStatus={false}
              />
            </>
          ) : null}
        </>
      )}
    </section>
  );
}
