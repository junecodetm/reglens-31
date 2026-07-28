import type { ClaimRecord, DocumentExtraction } from "./reglens-types";

interface RejectedClaimsProps {
  documents: DocumentExtraction[];
  rejectedCount: number;
}

function getRejectedClaims(documents: DocumentExtraction[]): ClaimRecord[] {
  return documents.flatMap((document) =>
    document.claims.filter((claim) => !claim.accepted),
  );
}

export function RejectedClaims({
  documents,
  rejectedCount,
}: RejectedClaimsProps) {
  const rejectedClaims = getRejectedClaims(documents);

  return (
    <section
      className="rejected-section"
      aria-labelledby="rejected-heading"
    >
      <h2 id="rejected-heading">Rejected claims ({rejectedCount})</h2>
      <p>
        These model-proposed claims failed exact verbatim verification against
        the source text and were rejected by the fail-closed provenance gate.
      </p>

      {rejectedClaims.length === 0 ? (
        <p className="empty-state">
          No rejected claim records are present in this snapshot.
        </p>
      ) : (
        <div className="rejected-list">
          {rejectedClaims.map((claim) => (
            <details className="rejected-item" key={claim.claim_id}>
              <summary>
                Rejected proposal from FR {claim.document_number}
              </summary>
              <div className="rejected-item-body">
                <blockquote>{claim.quote}</blockquote>
                <dl>
                  <div>
                    <dt>Rejection reason</dt>
                    <dd>{claim.rejection_reason ?? "Not provided"}</dd>
                  </div>
                  <div>
                    <dt>Document number</dt>
                    <dd>{claim.document_number}</dd>
                  </div>
                </dl>
              </div>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
