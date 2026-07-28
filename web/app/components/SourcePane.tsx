"use client";

import { useEffect, useRef } from "react";

import type { ClaimRecord, SourceTextState } from "./reglens-types";

interface SourcePaneProps {
  selectedClaim: ClaimRecord | null;
  sourceState: SourceTextState;
}

interface SourceSegments {
  before: string;
  highlighted: string;
  after: string;
}

function getSourceSegments(
  sourceText: string,
  claim: ClaimRecord,
): SourceSegments | null {
  // Offsets come from the fail-closed provenance gate, which matched the quote
  // under documented normalization (NFKC + whitespace collapse). Raw slices can
  // therefore differ from the quote in whitespace, so only bounds are checked.
  const { start, end } = claim;

  if (
    start === null ||
    end === null ||
    !Number.isInteger(start) ||
    !Number.isInteger(end) ||
    start < 0 ||
    end <= start ||
    end > sourceText.length
  ) {
    return null;
  }

  return {
    before: sourceText.slice(0, start),
    highlighted: sourceText.slice(start, end),
    after: sourceText.slice(end),
  };
}

export function SourcePane({
  selectedClaim,
  sourceState,
}: SourcePaneProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const markRef = useRef<HTMLElement>(null);
  const isCurrentDocument =
    selectedClaim !== null &&
    sourceState.status !== "idle" &&
    sourceState.documentNumber === selectedClaim.document_number;
  const readyText =
    isCurrentDocument && sourceState.status === "ready"
      ? sourceState.text
      : null;
  const sourceSegments =
    selectedClaim && readyText
      ? getSourceSegments(readyText, selectedClaim)
      : null;

  useEffect(() => {
    const panel = panelRef.current;
    const highlight = markRef.current;

    if (!panel || !highlight) {
      return;
    }

    const panelRect = panel.getBoundingClientRect();
    const highlightRect = highlight.getBoundingClientRect();
    const targetTop =
      panel.scrollTop +
      (highlightRect.top - panelRect.top) -
      (panel.clientHeight - highlightRect.height) / 2;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    panel.scrollTo({
      top: Math.max(0, targetTop),
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });
  }, [readyText, selectedClaim?.claim_id]);

  return (
    <section className="pane source-pane" aria-labelledby="source-heading">
      <h2 id="source-heading">Primary source</h2>

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
              <h3>Source document unavailable</h3>
              <p>{sourceState.message}</p>
            </div>
          ) : null}

          {readyText !== null ? (
            <>
              {!sourceSegments ? (
                <div className="error-state" role="alert">
                  <h3>Verified span unavailable</h3>
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

              <div
                ref={panelRef}
                className="source-document"
                tabIndex={0}
                role="region"
                aria-label="Source document text"
              >
                {sourceSegments ? (
                  <>
                    {sourceSegments.before}
                    <mark ref={markRef}>{sourceSegments.highlighted}</mark>
                    {sourceSegments.after}
                  </>
                ) : (
                  readyText
                )}
              </div>
            </>
          ) : null}
        </>
      )}
    </section>
  );
}
