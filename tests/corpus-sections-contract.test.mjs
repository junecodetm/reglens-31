import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const ROOT = new URL("../", import.meta.url);

async function read(relativePath) {
  return readFile(new URL(relativePath, ROOT), "utf8");
}

test("new corpus sections retain the required headings and explanatory copy", async () => {
  const [search, browse, crossRef] = await Promise.all([
    read("web/app/components/SearchSection.tsx"),
    read("web/app/components/BrowseSection.tsx"),
    read("web/app/components/CrossRefSection.tsx"),
  ]);

  assert.match(search, /Search the ingested corpus/);
  assert.match(
    search,
    /Lexical search over extracted obligations, U\.S\. Code sections, CFR part sections, and draft skeletons\. Exact-term matching against a precomputed index — no semantic ranking, no external service, and no model involvement\./,
  );
  assert.match(search, /Loading the search index…/);
  assert.match(
    search,
    /No matches in the ingested corpus for that query\./,
  );

  assert.match(browse, /Browse Title 31 \(ingested parts\)/);
  assert.match(
    browse,
    /Hierarchical navigation over the five ingested parts of 31 CFR \(as of the pinned snapshot date\), from part to section\. Selecting a section opens the part text at that location\. Paragraph-level drill-down is not built\./,
  );
  assert.match(browse, /Title 31 — Money and Finance: Treasury/);
  assert.match(
    browse,
    /Showing \$\{section\.designation\} within 31 CFR Part \$\{part\.part\}\./,
  );

  assert.match(crossRef, /Authority cross-references/);
  assert.match(
    crossRef,
    /Which U\.S\. Code sections each ingested CFR part cites as rulemaking authority, and which cited sections are shared across parts\. Retrieval over the parsed authority citations only — this is not a dependency, impact, or conflict analysis\. Citations that did not resolve in the pinned U\.S\. Code release are listed separately as coverage facts\./,
  );
  assert.match(crossRef, /By CFR part/);
  assert.match(crossRef, /By U\.S\. Code section/);
  assert.match(
    crossRef,
    /Only U\.S\. Code sections cited by more than one ingested part/,
  );
  assert.match(
    crossRef,
    /single-part authorities appear in the\s+per-part recap below\./,
  );
});

test("draft checklist includes APA structural checks and generation provenance", async () => {
  const drafts = await read("web/app/components/DraftsSection.tsx");

  for (const text of [
    "APA procedural elements (structural presence only)",
    "Authority citation present",
    "Basis-and-purpose elements present",
    "Comment-period / effective-date reference",
    "Amendatory verb forms demonstrated (add / revise / remove-and-reserve)",
    "These checks verify the structural presence of required elements in the skeleton. They are not a determination of legal sufficiency.",
    "Generation provenance",
    "Model-generated fields",
    "System prompt SHA-256",
    "User prompt SHA-256",
    // Truncated before the closing paren: the full dt label wraps across
    // source lines, and this check matches raw source text.
    "Source part snapshot SHA-256 (context of record",
  ]) {
    assert.ok(drafts.includes(text), `Missing required DraftsSection copy: ${text}`);
  }

  // The scope-of-model-authorship disclosure lives in the page lead.
  const draftsPage = await read("web/app/drafts/page.tsx");
  assert.ok(
    draftsPage.includes("deterministic template output"),
    "Missing required drafts lead copy: deterministic template output",
  );
});
