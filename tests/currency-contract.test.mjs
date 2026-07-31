import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const SOURCE = readFileSync(
  join(ROOT, "web", "app", "components", "CurrencySection.tsx"),
  "utf8",
);
// JSX wraps prose across lines, so copy assertions run against collapsed text.
const COPY = SOURCE.replace(/\s+/g, " ");

function currency() {
  return JSON.parse(
    readFileSync(join(ROOT, "web", "public", "data", "currency.json"), "utf8"),
  );
}

/**
 * The currency surface reports how far the pinned corpus has drifted from the
 * live regulation. It is computed at build time, so the deployed page remains
 * same-origin and the number is reproducible. It records drift without
 * characterising what an amendment means.
 */
test("the currency artifact is internally consistent", () => {
  const data = currency();

  assert.equal(
    data.total_sections,
    data.parts.reduce((sum, part) => sum + part.census_count, 0),
  );
  assert.equal(
    data.total_amended_since_snapshot,
    data.parts.reduce((sum, part) => sum + part.amended_since_snapshot, 0),
  );
  assert.match(data.snapshot_date, /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(data.parts.length, 5);
});

test("both currency surfaces render nothing until the artifact is ready", () => {
  const guards = SOURCE.match(/state\.status !== "ready"/g) ?? [];

  assert.equal(guards.length, 2, "the table and the footer note must both guard");
  assert.equal(
    (SOURCE.match(/return null;/g) ?? []).length,
    2,
    "a missing artifact must degrade to silence, not to an error",
  );
});

test("the currency section states that the comparison is build-time only", () => {
  assert.match(COPY, /build time/);
  assert.match(COPY, /makes no network call/);
  assert.match(COPY, /versioner API/);
});

test("the currency copy records drift without characterising it", () => {
  // The neutrality rules prohibit judgments about an amendment's implications.
  for (const forbidden of [
    /\bout of date\b/i,
    /\bstale\b/i,
    /\bobsolete\b/i,
    /\bno longer valid\b/i,
    /\bneeds review\b/i,
    /\bshould be updated\b/i,
  ]) {
    assert.doesNotMatch(COPY, forbidden);
  }
  assert.match(COPY, /not interpreted/);
});

test("the table is accessible: a caption and scoped headers", () => {
  assert.match(SOURCE, /caption="Section census and upstream amendments/);
  assert.match(SOURCE, /scope="col"/);
  assert.match(SOURCE, /scope="row"/);
});

test("no currency number is written into the component", () => {
  const data = currency();
  const counts = [
    data.total_sections,
    data.total_amended_since_snapshot,
    ...data.parts.map((part) => part.census_count),
  ];

  for (const count of counts) {
    assert.doesNotMatch(
      SOURCE,
      new RegExp(`\\b${count}\\b`),
      `a currency count is hard-coded in the component`,
    );
  }
  assert.doesNotMatch(SOURCE, /\d{4}-\d{2}-\d{2}/, "the pinned date is hard-coded");
});
