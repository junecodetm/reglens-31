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
  ["obligations", "Extracted obligations", "Extracted obligations"],
  ["authorities", "Statutory authority", "Statutory authority"],
  ["drafts", "Draft rule skeletons", "Draft skeletons"],
  ["evaluation", "Evaluation (provisional)", "Evaluation"],
  ["sources", "Search &amp; browse the corpus", "Search &amp; browse"],
  ["about", "About this demonstration", "About &amp; provenance"],
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

test("every route emits exactly one page-lead paragraph, except the Overview", () => {
  for (const [route] of ROUTES) {
    const html = readPage(route);
    const leadCount = (html.match(/class="page-lead"/g) ?? []).length;

    if (route === "") {
      assert.equal(
        leadCount,
        0,
        "Overview uses its own hero copy, not PageHeader's lead prop",
      );
    } else {
      assert.equal(
        leadCount,
        1,
        `${route}: expected exactly one page-lead paragraph`,
      );
    }
  }
});

test("the Overview keeps the mockup framing, the guided example, and the legacy-hash forwarder", () => {
  const html = readPage("");

  assert.ok(html.includes("About this demonstration"));
  assert.ok(html.includes("Regulatory Reform Tool"));
  assert.ok(html.includes("See it work"));

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
    ["#extraction", "/obligations"],
    ["#rejected-claims", "/obligations#rejected"],
    ["#explore", "/sources"],
    ["#ogc01", "/authorities"],
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
