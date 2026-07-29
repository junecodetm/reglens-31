import assert from "node:assert/strict";
import test from "node:test";

import {
  encodePathSegments,
  rankSearchUnits,
  tokenizeSearchQuery,
  type SearchIndexData,
} from "../web/app/components/search-utils.ts";

const INDEX: SearchIndexData = {
  tokenizer: "test fixture",
  avgdl: 10,
  units: [
    {
      id: "claim:0",
      type: "claim",
      label: "Alpha zero",
      ref: "document-0",
      length: 10,
      snippet: "Alpha zero",
    },
    {
      id: "claim:1",
      type: "claim",
      label: "Alpha one",
      ref: "document-1",
      length: 10,
      snippet: "Alpha one",
    },
    {
      id: "draft:2",
      type: "draft",
      label: "Beta draft",
      ref: "beta draft.txt",
      length: 20,
      snippet: "Beta beta beta",
    },
  ],
  postings: {
    alpha: [
      [1, 1],
      [0, 1],
    ],
    beta: [[2, 3]],
  },
};

test("tokenizer applies NFKC, lowercases, and preserves internal dotted tokens", () => {
  assert.deepEqual(
    tokenizeSearchQuery("ＡＢＣ 18 U.S.C. 3.14 foo..bar"),
    ["abc", "18", "u.s.c", "3.14", "foo", "bar"],
  );
});

test("BM25 uses unit-index order as the stable tie-break", () => {
  const results = rankSearchUnits(INDEX, "alpha");

  assert.deepEqual(
    results.map((result) => result.unitIndex),
    [0, 1],
  );
  assert.ok(Math.abs(results[0].score - Math.log(1.6)) < 1e-12);
});

test("BM25 sums repeated query tokens and skips absent postings", () => {
  const repeated = rankSearchUnits(INDEX, "alpha alpha");
  const absent = rankSearchUnits(INDEX, "missing");

  assert.ok(Math.abs(repeated[0].score - 2 * Math.log(1.6)) < 1e-12);
  assert.deepEqual(absent, []);
});

test("BM25 ranks by score and respects the result limit", () => {
  const results = rankSearchUnits(INDEX, "alpha beta", 1);

  assert.equal(results.length, 1);
  assert.equal(results[0].unitIndex, 2);
});

test("BM25 favors shorter units at equal term frequency", () => {
  const index: SearchIndexData = {
    tokenizer: "test fixture",
    avgdl: 10,
    units: [
      { ...INDEX.units[0], length: 5 },
      { ...INDEX.units[1], length: 20 },
    ],
    postings: {
      alpha: [
        [0, 1],
        [1, 1],
      ],
    },
  };

  const results = rankSearchUnits(index, "alpha");

  assert.deepEqual(
    results.map((result) => result.unitIndex),
    [0, 1],
  );
  assert.ok(results[0].score > results[1].score);
});

test("BM25 term-frequency gains saturate", () => {
  const index: SearchIndexData = {
    tokenizer: "test fixture",
    avgdl: 10,
    units: [
      { ...INDEX.units[0] },
      { ...INDEX.units[0], id: "claim:tf-2" },
      { ...INDEX.units[0], id: "claim:tf-4" },
    ],
    postings: {
      alpha: [
        [0, 1],
        [1, 2],
        [2, 4],
      ],
    },
  };

  const results = rankSearchUnits(index, "alpha");
  const scoresByIndex = new Map(
    results.map((result) => [result.unitIndex, result.score]),
  );
  const firstGain = scoresByIndex.get(1)! - scoresByIndex.get(0)!;
  const secondGain = scoresByIndex.get(2)! - scoresByIndex.get(1)!;

  assert.ok(scoresByIndex.get(2)! > scoresByIndex.get(1)!);
  assert.ok(scoresByIndex.get(1)! > scoresByIndex.get(0)!);
  assert.ok(secondGain < firstGain);
});

test("BM25 returns at most the default top 20 in unit-index order on ties", () => {
  const units = Array.from({ length: 25 }, (_, unitIndex) => ({
    ...INDEX.units[0],
    id: `claim:${unitIndex}`,
  }));
  const index: SearchIndexData = {
    tokenizer: "test fixture",
    avgdl: 10,
    units,
    postings: {
      alpha: units.map((_, unitIndex) => [24 - unitIndex, 1]),
    },
  };

  const results = rankSearchUnits(index, "alpha");

  assert.equal(results.length, 20);
  assert.deepEqual(
    results.map((result) => result.unitIndex),
    Array.from({ length: 20 }, (_, unitIndex) => unitIndex),
  );
});

test("path encoding preserves slashes while encoding each segment", () => {
  assert.equal(
    encodePathSegments("usc/a b/#.txt"),
    "usc/a%20b/%23.txt",
  );
});
