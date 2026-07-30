export interface CfrSectionRef {
  part: number;
  start: number;
  end: number;
}

interface SearchUnitBase {
  id: string;
  label: string;
  length: number;
  snippet: string;
}

export type SearchUnit =
  | (SearchUnitBase & { type: "claim"; ref: string })
  | (SearchUnitBase & { type: "usc"; ref: string })
  | (SearchUnitBase & { type: "cfr-section"; ref: CfrSectionRef })
  | (SearchUnitBase & { type: "draft"; ref: string });

export interface SearchIndexData {
  tokenizer: string;
  avgdl: number;
  units: SearchUnit[];
  postings: Record<string, Array<[number, number]>>;
}

export interface RankedSearchResult {
  unitIndex: number;
  score: number;
  unit: SearchUnit;
}

export type SearchUnitCounts = Record<SearchUnit["type"], number>;

const BM25_K1 = 1.2;
const BM25_B = 0.75;

export function countSearchUnitsByType(
  index: SearchIndexData,
): SearchUnitCounts {
  return index.units.reduce<SearchUnitCounts>(
    (counts, unit) => {
      counts[unit.type] += 1;
      return counts;
    },
    {
      claim: 0,
      usc: 0,
      "cfr-section": 0,
      draft: 0,
    },
  );
}

export function formatPartHeading(part: number, heading: string): string {
  const trimmedHeading = heading.trim();
  const repeatedPartPrefix = new RegExp(
    `^PART\\s+${part}\\s*(?:[-\\u2012-\\u2015\\u2212]+\\s*)?`,
    "i",
  );
  const withoutRepeatedPart = trimmedHeading
    .replace(repeatedPartPrefix, "")
    .trim();
  const title = withoutRepeatedPart || trimmedHeading;
  const lowercaseTitle = title.toLocaleLowerCase("en-US");
  const uppercaseTitle = title.toLocaleUpperCase("en-US");
  const isAllCaps =
    title === uppercaseTitle && lowercaseTitle !== uppercaseTitle;

  if (!isAllCaps) {
    return title;
  }

  return lowercaseTitle.replace(/\b[a-z]/g, (letter) =>
    letter.toLocaleUpperCase("en-US"),
  );
}

export function tokenizeSearchQuery(query: string): string[] {
  // Python casefold and JS toLowerCase can disagree outside ASCII (e.g. casefold('ß')→'ss'), but neither path yields differing ASCII tokens for this corpus, so index and query tokens agree.
  return (
    query
      .normalize("NFKC")
      .toLowerCase()
      .match(/[a-z0-9]+(?:\.[a-z0-9]+)*/g) ?? []
  );
}

export function rankSearchUnits(
  index: SearchIndexData,
  query: string,
  limit = 20,
): RankedSearchResult[] {
  const scores = new Map<number, number>();
  const documentCount = index.units.length;

  for (const token of tokenizeSearchQuery(query)) {
    const posting = index.postings[token];

    if (!posting) {
      continue;
    }

    const documentFrequency = posting.length;
    const inverseDocumentFrequency = Math.log(
      1 +
        (documentCount - documentFrequency + 0.5) /
          (documentFrequency + 0.5),
    );

    for (const [unitIndex, termFrequency] of posting) {
      const unit = index.units[unitIndex];

      if (!unit) {
        continue;
      }

      const lengthRatio =
        index.avgdl > 0 ? unit.length / index.avgdl : 0;
      const denominator =
        termFrequency +
        BM25_K1 * (1 - BM25_B + BM25_B * lengthRatio);
      const contribution =
        inverseDocumentFrequency *
        ((termFrequency * (BM25_K1 + 1)) / denominator);

      scores.set(unitIndex, (scores.get(unitIndex) ?? 0) + contribution);
    }
  }

  return [...scores.entries()]
    .map(([unitIndex, score]) => ({
      unitIndex,
      score,
      unit: index.units[unitIndex],
    }))
    .sort(
      (left, right) =>
        right.score - left.score || left.unitIndex - right.unitIndex,
    )
    .slice(0, Math.max(0, Math.floor(limit)));
}

export function encodePathSegments(path: string): string {
  const segments = path.split("/");

  // Mirror the Python export's snapshot-filename guard.
  if (
    segments.some(
      (segment) => segment === "" || segment === "." || segment === "..",
    )
  ) {
    throw new Error(`Unsafe path segment in ${path}`);
  }

  return segments.map(encodeURIComponent).join("/");
}
