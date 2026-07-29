import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

// §333 non-affiliation string that must appear on EVERY emitted page
// (mirrored by the disclaimer-and-framing-guard loop in ci.yml).
const DISCLAIMER =
  "Not affiliated with, endorsed by, or representing the U.S. Department of the Treasury";

// route → sole h1 text and sidebar label carrying aria-current on that page.
const ROUTES = [
  ["", "RegLens-31", "Overview"],
  ["about", "About this demonstration", "About this demonstration"],
  ["extraction/claims", "Extracted obligations", "Claims &amp; sources"],
  ["extraction/rejected", "Rejected claims", "Rejected claims"],
  ["explore/search", "Search the ingested corpus", "Corpus search"],
  ["explore/browse", "Browse Title 31 (ingested parts)", "Browse Title 31"],
  [
    "explore/cross-references",
    "Authority cross-references",
    "Authority cross-references",
  ],
  ["ogc01/authority", "Statutory authority", "Authority citations"],
  [
    "ogc01/grounding",
    "Grounding markers (two-sided)",
    "Grounding markers",
  ],
  ["ogc01/drafts", "Draft rule skeletons", "Draft skeletons"],
  ["evaluation", "Evaluation — core metrics (provisional)", "Core metrics"],
  [
    "evaluation/ogc01",
    "Evaluation — authority, grounding, and drafts (provisional)",
    "OGC-01 modules",
  ],
];

function readPage(route) {
  const path = join(ROOT, "web", "out", route, "index.html");
  assert.ok(existsSync(path), `missing export: ${route || "/"}/index.html`);
  return readFileSync(path, "utf8");
}

test("every route emits, carries the §333 disclaimer, and has exactly one h1", () => {
  for (const [route, h1Text] of ROUTES) {
    const html = readPage(route);

    assert.ok(
      html.includes(DISCLAIMER),
      `${route || "/"}: §333 disclaimer missing`,
    );

    const h1s = [...html.matchAll(/<h1[^>]*>(.*?)<\/h1>/gs)];
    assert.equal(h1s.length, 1, `${route || "/"}: expected exactly one h1`);
    assert.ok(
      h1s[0][1].includes(h1Text),
      `${route || "/"}: h1 should read "${h1Text}", got "${h1s[0][1].slice(0, 80)}"`,
    );
  }
});

test("the sidebar marks each page's own link with aria-current", () => {
  for (const [route, , navLabel] of ROUTES) {
    const html = readPage(route);
    const current = html.match(
      /<a[^>]*aria-current="page"[^>]*>(.*?)<\/a>/s,
    );

    assert.ok(current, `${route || "/"}: no aria-current link prerendered`);
    assert.ok(
      current[1].includes(navLabel),
      `${route || "/"}: aria-current should sit on "${navLabel}", got "${current[1].slice(0, 60)}"`,
    );
  }
});

test("the Overview keeps the mockup framing and the legacy-hash forwarder", () => {
  const html = readPage("");

  assert.ok(html.includes("About this demonstration"));
  assert.ok(html.includes("Regulatory Reform Tool"));

  const overview = readFileSync(
    join(ROOT, "web", "app", "OverviewContent.tsx"),
    "utf8",
  );
  const redirect = readFileSync(
    join(ROOT, "web", "app", "components", "shell", "LegacyHashRedirect.tsx"),
    "utf8",
  );

  assert.match(overview, /<LegacyHashRedirect \/>/);
  for (const [hash, target] of [
    ["#about", "/about"],
    ["#extraction", "/extraction/claims"],
    ["#rejected-claims", "/extraction/rejected"],
    ["#explore", "/explore/search"],
    ["#ogc01", "/ogc01/authority"],
    ["#evaluation", "/evaluation"],
  ]) {
    assert.ok(
      redirect.includes(`"${hash}": "${target}"`),
      `legacy hash map should forward ${hash} → ${target}`,
    );
  }
});

test("both evaluation payloads keep the verbatim provisional honesty label", () => {
  for (const file of ["eval.json", "ogc01-eval.json"]) {
    const payload = readFileSync(
      join(ROOT, "web", "public", "data", file),
      "utf8",
    );
    assert.ok(
      payload.includes("Provisional — machine-proposed labels"),
      `${file}: provisional label missing`,
    );
  }
});
