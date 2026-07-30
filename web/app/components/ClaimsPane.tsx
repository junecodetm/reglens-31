"use client";

import { useState } from "react";

import type {
  ClaimRecord,
  DocumentExtraction,
} from "./reglens-types";

export const CLAIM_PREVIEW_LIMIT = 25;

interface ClaimsPaneProps {
  documents: DocumentExtraction[];
  selectedClaimId: string | null;
  onSelectClaim: (claim: ClaimRecord) => void;
  standalone?: boolean;
}

export function ClaimsPane({
  documents,
  selectedClaimId,
  onSelectClaim,
  standalone = false,
}: ClaimsPaneProps) {
  const groups = documents
    .map((document) => ({
      document,
      acceptedClaims: document.claims.filter((claim) => claim.accepted),
    }))
    .filter(({ acceptedClaims }) => acceptedClaims.length > 0);
  const [expandedDocumentIds, setExpandedDocumentIds] = useState<Set<string>>(
    () => new Set(),
  );
  const DocumentHeading = standalone ? "h2" : "h4";

  function toggleAllClaims(documentId: string): void {
    setExpandedDocumentIds((current) => {
      const expanded = new Set(current);

      if (expanded.has(documentId)) {
        expanded.delete(documentId);
      } else {
        expanded.add(documentId);
      }

      return expanded;
    });
  }

  return (
    <section
      className="pane claims-pane"
      aria-label={standalone ? "Extracted obligations" : undefined}
      aria-labelledby={standalone ? undefined : "claims-heading"}
    >
      {!standalone ? (
        <h3 id="claims-heading">Extracted obligations</h3>
      ) : null}

      {groups.length === 0 ? (
        <p className="empty-state">
          No claims passed the provenance gate in this snapshot.
        </p>
      ) : (
        <div className="document-groups">
          {groups.map(({ document, acceptedClaims }) => {
            const isExpanded = expandedDocumentIds.has(
              document.document_sha256,
            );
            const displayedClaims = isExpanded
              ? acceptedClaims
              : acceptedClaims.slice(0, CLAIM_PREVIEW_LIMIT);
            const claimListId = `claims-${document.document_sha256}`;

            return (
              <article
                className="document-group"
                key={document.document_sha256}
              >
                <DocumentHeading>
                  <span>{document.document_title}</span>
                  <a href={document.document_url} className="document-link">
                    FR {document.document_number}
                    <span aria-hidden="true"> ↗</span>
                  </a>
                </DocumentHeading>

                <ul className="claim-list" id={claimListId}>
                  {displayedClaims.map((claim) => {
                    const isSelected = claim.claim_id === selectedClaimId;

                    return (
                      <li key={claim.claim_id}>
                        <button
                          type="button"
                          className="claim-button"
                          aria-pressed={isSelected}
                          onClick={() => onSelectClaim(claim)}
                        >
                          <span className="claim-button-topline">
                            <span className="claim-summary">
                              {claim.summary}
                            </span>
                            {isSelected ? (
                              <span
                                className="selected-indicator"
                                aria-hidden="true"
                              >
                                Selected
                              </span>
                            ) : null}
                          </span>

                          <span className="claim-metadata">
                            <span
                              className="obligation-tag"
                              data-obligation-type={claim.obligation_type}
                            >
                              {claim.obligation_type}
                            </span>
                            <span>
                              <span className="metadata-label">
                                Affected party:
                              </span>{" "}
                              {claim.affected_party}
                            </span>
                            {claim.effective_date ? (
                              <span>
                                <span className="metadata-label">
                                  Effective:
                                </span>{" "}
                                <time dateTime={claim.effective_date}>
                                  {claim.effective_date}
                                </time>
                              </span>
                            ) : null}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>

                {acceptedClaims.length > CLAIM_PREVIEW_LIMIT ? (
                  <button
                    type="button"
                    className="usa-button usa-button--outline"
                    aria-expanded={isExpanded}
                    aria-controls={claimListId}
                    onClick={() =>
                      toggleAllClaims(document.document_sha256)
                    }
                  >
                    {isExpanded
                      ? "Show fewer accepted claims"
                      : `Show all ${acceptedClaims.length} accepted claims`}
                  </button>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
