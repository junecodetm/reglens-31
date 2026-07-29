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
    /Shared authorities \(cited by more than one part\) appear first\./,
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
    "Model-generated fields:",
    "Model, decoding parameters, and SHA-256 digests of the prompts sent to the model and of the source part snapshot of record. Everything else in the skeleton is deterministic template output.",
  ]) {
    assert.ok(drafts.includes(text), `Missing required DraftsSection copy: ${text}`);
  }
});

test("page mounts the new sections in the required order", async () => {
  const page = await read("web/app/page.tsx");
  const collapsibleIndex = (id) =>
    new RegExp(`<CollapsibleSection\\s+id="${id}"`).exec(page)?.index ??
    -1;
  const about = page.indexOf("<AboutSection");
  const extraction = collapsibleIndex("extraction");
  const explore = collapsibleIndex("explore");
  const ogc01 = collapsibleIndex("ogc01");
  const evaluation = collapsibleIndex("evaluation");
  const source = page.indexOf("<SourcePane");
  const rejected = page.indexOf("<RejectedClaims");
  const search = page.indexOf("<SearchSection");
  const browse = page.indexOf("<BrowseSection");
  const crossRef = page.indexOf("<CrossRefSection");
  const authority = page.indexOf("<AuthoritySection");
  const grounding = page.indexOf("<GroundingSection");
  const drafts = page.indexOf("<DraftsSection");
  const evalSection = page.indexOf("<EvalSection");
  const ogc01Eval = page.indexOf("<Ogc01EvalSection");

  for (const index of [
    about,
    extraction,
    explore,
    ogc01,
    evaluation,
    source,
    rejected,
    search,
    browse,
    crossRef,
    authority,
    grounding,
    drafts,
    evalSection,
    ogc01Eval,
  ]) {
    assert.ok(index >= 0);
  }

  assert.ok(about < extraction);
  assert.ok(extraction < source);
  assert.ok(source < rejected);
  assert.ok(rejected < explore);
  assert.ok(explore < search);
  assert.ok(search < browse);
  assert.ok(browse < crossRef);
  assert.ok(crossRef < ogc01);
  assert.ok(ogc01 < authority);
  assert.ok(authority < grounding);
  assert.ok(grounding < drafts);
  assert.ok(drafts < evaluation);
  assert.ok(evaluation < evalSection);
  assert.ok(evalSection < ogc01Eval);
});

test("page navigation and new attribution copy retain the required contract", async () => {
  const [page, pageNav] = await Promise.all([
    read("web/app/page.tsx"),
    read("web/app/components/PageNav.tsx"),
  ]);
  const disclaimer = page.indexOf("<DisclaimerBand");
  const navigation = page.indexOf("<PageNav");
  const about = page.indexOf("<AboutSection");
  const header = page.slice(
    page.indexOf('<header className="site-header">'),
    page.indexOf("</header>"),
  );
  const footer = page.slice(
    page.indexOf('<footer className="site-footer">'),
    page.indexOf("</footer>"),
  );
  const heroMockupLine =
    "An independent working mockup aligned to U.S. Treasury AI use case OGC-01 (“Regulatory Reform Tool,” Treasury public AI Use Case Inventory) — see About this demonstration below.";
  const footerAttribution =
    "Use-case framing: Treasury AI Use Case Inventory (U.S. Government work) — see About this demonstration.";

  assert.ok(disclaimer >= 0);
  assert.ok(disclaimer < navigation);
  assert.ok(navigation < about);
  assert.match(pageNav, /<nav[^>]+aria-label="Section navigation"/);

  for (const [href, label] of [
    ["#about", "About"],
    ["#extraction", "Extraction"],
    ["#explore", "Explore"],
    ["#ogc01", "OGC-01 modules"],
    ["#evaluation", "Evaluation"],
  ]) {
    assert.match(
      pageNav,
      new RegExp(`href="${href}"[^>]*>\\s*${label}\\s*</a>`),
    );
  }

  assert.ok(page.includes(heroMockupLine));
  assert.ok(header.includes("<p>{HERO_MOCKUP_LINE}</p>"));
  assert.ok(page.includes(footerAttribution));
  assert.ok(footer.includes("<p>{FOOTER_ATTRIBUTION}</p>"));
});

test("hash navigation waits for disclosure and upstream layout readiness", async () => {
  const [page, collapsible, about] = await Promise.all([
    read("web/app/page.tsx"),
    read("web/app/components/ui/CollapsibleSection.tsx"),
    read("web/app/components/AboutSection.tsx"),
  ]);

  assert.match(collapsible, /onForceOpen/);
  assert.match(page, /markHashTargetOpen/);
  assert.match(page, /aboutInventorySettled/);
  assert.match(page, /new MutationObserver/);
  assert.match(about, /about-inventory-loading/);
  assert.match(page, /event\.preventDefault\(\)/);
  assert.match(
    page,
    /current\?\.sequence === sequence \? null : current/,
  );
});
