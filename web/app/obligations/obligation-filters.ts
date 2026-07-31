import type {
  ClaimRecord,
  GroundingData,
} from "../components/reglens-types";

type ClaimView = "accepted" | "rejected";

function normalizeFilterValue(value: string): string {
  return value.trim().toLowerCase();
}

export function filterClaims(
  claims: ClaimRecord[],
  view: ClaimView,
  obligationType: string,
  affectedParty: string,
  filterText: string,
): ClaimRecord[] {
  const hasObligationTypeFilter = obligationType.trim() !== "";
  const normalizedParty = normalizeFilterValue(affectedParty);
  const normalizedText = normalizeFilterValue(filterText);

  return claims.filter((claim) => {
    const hasRequestedStatus =
      view === "accepted" ? claim.accepted : !claim.accepted;

    if (!hasRequestedStatus) {
      return false;
    }

    if (
      hasObligationTypeFilter &&
      claim.obligation_type !== obligationType
    ) {
      return false;
    }

    if (
      normalizedParty !== "" &&
      normalizeFilterValue(claim.affected_party) !== normalizedParty
    ) {
      return false;
    }

    if (normalizedText === "") {
      return true;
    }

    return (
      claim.summary.toLowerCase().includes(normalizedText) ||
      claim.quote.toLowerCase().includes(normalizedText)
    );
  });
}

export function resolveReviewPart(
  documentNumber: string,
  grounding: Pick<GroundingData, "rules"> | null,
): number | null {
  const directMatch = /^31-CFR-(\d+)$/.exec(documentNumber);

  if (directMatch !== null) {
    return Number(directMatch[1]);
  }

  const sourceRule = grounding?.rules.find(
    (rule) =>
      rule.document_number === documentNumber &&
      rule.source_for_part !== null,
  );

  return sourceRule?.source_for_part ?? null;
}
