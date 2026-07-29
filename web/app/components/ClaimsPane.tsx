import type {
  ClaimRecord,
  DocumentExtraction,
} from "./reglens-types";

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
  const DocumentHeading = standalone ? "h2" : "h4";

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
          {groups.map(({ document, acceptedClaims }) => (
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

              <ul className="claim-list">
                {acceptedClaims.map((claim) => {
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
                          <span className="claim-summary">{claim.summary}</span>
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
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
