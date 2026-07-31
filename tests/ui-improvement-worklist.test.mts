import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire, registerHooks } from "node:module";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const WEB_ROOT = join(ROOT, "web");

function read(relativePath: string): string {
  return readFileSync(join(WEB_ROOT, relativePath), "utf8");
}

const requireFromWeb = createRequire(
  new URL("../web/package.json", import.meta.url),
);
const ts = requireFromWeb("typescript");

registerHooks({
  load(url, context, nextLoad) {
    if (!url.endsWith(".tsx")) {
      return nextLoad(url, context);
    }

    const source = readFileSync(new URL(url), "utf8");
    const output = ts.transpileModule(source, {
      compilerOptions: {
        jsx: ts.JsxEmit.ReactJSX,
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
      },
      fileName: new URL(url).pathname,
    });

    return {
      format: "module",
      shortCircuit: true,
      source: output.outputText,
    };
  },
});

test("disclaimer preserves the USWDS inline margin that clears its icon", () => {
  const css = read("app/globals.css");
  const rule = css.match(
    /\.disclaimer-alert \.usa-alert__text\s*\{([\s\S]*?)\}/,
  );

  assert.ok(rule, "the disclaimer text override should exist");
  assert.match(rule[1], /margin-block:\s*0;/);
  assert.doesNotMatch(rule[1], /margin:\s*0;/);
});

test("authority range grouping keeps direct citations visible and partitions silent range members", async () => {
  const module = await import(
    "../web/app/components/crossref-utils.ts"
  );
  const groupAuthoritySections = (
    module as unknown as {
      groupAuthoritySections?: (part: any) => Array<{
        range: string | null;
        sections: any[];
        visibleSections: any[];
        silentSections: any[];
      }>;
    }
  ).groupAuthoritySections;

  assert.equal(typeof groupAuthoritySections, "function");
  if (!groupAuthoritySections) return;

  const section = (
    uscSection: string,
    classification: string,
    verbQuote: string | null,
  ) => ({
    usc_title: 31,
    usc_section: uscSection,
    classification,
    verb_quote: verbQuote,
  });
  const part = {
    citations: [
      {
        kind: "usc-section",
        usc_title: 31,
        usc_section: "1",
        from_range: null,
      },
      ...["10", "11", "12", "13", "14"].map((uscSection) => ({
        kind: "usc-section",
        usc_title: 31,
        usc_section: uscSection,
        from_range: "31 U.S.C. 10-14",
      })),
    ],
    resolved: [
      section("1", "silent", null),
      section("10", "mandatory", "shall"),
      section("11", "discretionary", null),
      section("12", "silent", "may"),
      section("13", "silent", null),
      section("14", "unresolved", null),
    ],
  };

  const groups = groupAuthoritySections(part);

  assert.deepEqual(
    groups.map((group) => ({
      range: group.range,
      all: group.sections.map((item) => item.usc_section),
      visible: group.visibleSections.map((item) => item.usc_section),
      silent: group.silentSections.map((item) => item.usc_section),
    })),
    [
      {
        range: null,
        all: ["1"],
        visible: ["1"],
        silent: [],
      },
      {
        range: "31 U.S.C. 10-14",
        all: ["10", "11", "12", "13", "14"],
        visible: ["10", "11", "12"],
        silent: ["13", "14"],
      },
    ],
  );
});

test("shared authorities precede a collapsed per-part recap", () => {
  const source = read("app/components/CrossRefSection.tsx");
  const aggregate = source.indexOf('id="cross-ref-by-usc-heading"');
  const recap = source.indexOf("Per-part authority recap");

  assert.ok(aggregate >= 0, "shared-authority aggregation should exist");
  assert.ok(recap > aggregate, "the per-part recap should follow aggregation");
  assert.match(source, /<ExpandableGroup/);
  assert.match(source, /reference\.parts\.length\s*>\s*1/);
});

test("obligations preview, sticky pane, and narrow-screen focus movement are explicit", () => {
  const explorer = read("app/obligations/ObligationsExplorer.tsx");
  const sourcePane = read("app/components/SourcePane.tsx");
  const css = read("app/globals.css");

  assert.match(explorer, /CLAIM_PREVIEW_LIMIT\s*=\s*25/);
  assert.match(explorer, /Show all \$\{/);
  assert.match(explorer, /\.slice\(0,\s*CLAIM_PREVIEW_LIMIT\)/);
  assert.match(explorer, /aria-expanded=/);
  assert.match(explorer, /aria-controls=/);
  assert.match(explorer, /Show fewer/);
  assert.match(
    explorer,
    /matchMedia\("\(prefers-reduced-motion: reduce\)"\)/,
  );
  assert.match(explorer, /\.scrollIntoView\(\{/);
  assert.match(explorer, /behavior:\s*prefersReducedMotion\s*\?\s*"auto"\s*:\s*"smooth"/);
  assert.match(explorer, /\.focus\(\{\s*preventScroll:\s*true\s*\}\)/);
  assert.match(sourcePane, /tabIndex=\{-1\}/);
  assert.match(
    css,
    /@media \(min-width:\s*48rem\)[\s\S]*?\.two-pane-grid > \.source-pane\s*\{[\s\S]*?position:\s*sticky;[\s\S]*?max-height:\s*calc\(100vh - [^)]+\);[\s\S]*?overflow-y:\s*auto;/,
  );
});

test("document picker shortens point-in-time labels without hardcoding counts", async () => {
  const module = await import(
    "../web/app/components/DocumentPicker.tsx"
  );
  const formatDocumentOptionLabel = (
    module as unknown as {
      formatDocumentOptionLabel?: (document: any) => string;
    }
  ).formatDocumentOptionLabel;

  assert.equal(typeof formatDocumentOptionLabel, "function");
  if (!formatDocumentOptionLabel) return;

  assert.equal(
    formatDocumentOptionLabel({
      document_title: "31 CFR Part 223 (point-in-time 2026-07-01)",
      accepted_count: 148,
      rejected_count: 1,
    }),
    "31 CFR Part 223 (2026-07-01)",
  );
  assert.equal(
    formatDocumentOptionLabel({
      document_title: "A Federal Register document",
      accepted_count: 9,
      rejected_count: 4,
    }),
    "A Federal Register document",
  );

  const source = read("app/components/DocumentPicker.tsx");
  assert.match(source, /normalizedLabelCounts/);
  assert.match(source, /document\.document_number/);
  assert.match(source, /normalizedLabelCounts\.get\(optionLabel\)/);
});

test("draft checklist summary is data-derived and itemized checks are disclosed", () => {
  const source = read("app/components/DraftsSection.tsx");

  assert.match(source, /const checklistChecks = \[/);
  // The aggregate "Overall passed" row must be excluded from the summary
  // count (it stays in the itemized list) so one real failure is not
  // double-counted through the aggregate.
  assert.match(
    source,
    /const substantiveChecks = checklistChecks\.filter\(\s*\(\[label\]\) => label !== "Overall passed",?\s*\)/,
  );
  assert.match(
    source,
    /passed:\s*substantiveChecks\.filter\(\(\[, value\]\) => value\)\.length/,
  );
  assert.match(source, /total:\s*substantiveChecks\.length/);
  assert.match(source, /\$\{summary\.passed\}\/\$\{summary\.total\} checks passed/);
  assert.match(source, /Show itemized checklist/);
  assert.match(source, />Load and show draft text</);
  assert.match(source, /aria-label=\{`Load and show draft text for \$\{label\}`\}/);
});

test("draft parameters stay optional and live output remains fail-visible", () => {
  const source = read("app/components/DraftsSection.tsx");
  const types = read("app/components/reglens-types.ts");

  assert.match(
    source,
    /useLazyJson<DraftInputs>\("\/data\/draft-inputs\.json"/,
  );
  for (const label of [
    "CFR part",
    "NPRM",
    "Final rule",
    "Policy objective (optional)",
    "Generate opening narrative (live)",
  ]) {
    assert.ok(source.includes(label), `missing draft control label: ${label}`);
  }
  assert.match(source, /maxLength=\{500\}/);
  assert.match(source, /aria-live="polite"/);
  assert.match(source, /requestLiveDraft\(/);
  assert.match(source, /assembleSkeleton\(/);
  assert.match(source, /checkLiveDraft\(/);
  assert.match(source, /Live model output \(\{liveResult\.model\}\)/);
  assert.match(source, /Checks requiring review:/);
  assert.match(source, /containerId=\{`draft-\$\{key\}`\}/);
  assert.ok(
    source.includes(
      "The shared free-tier generation limit is momentarily exhausted. The committed, fully conformance-gated draft for these parameters is shown instead.",
    ),
  );
  assert.ok(
    source.includes(
      "Live generation is unavailable. The committed, fully conformance-gated draft for these parameters is shown instead.",
    ),
  );
  assert.match(types, /provider\?: string/);
  assert.match(types, /num_ctx: number \| null/);
  assert.match(types, /num_predict: number \| null/);
  assert.match(types, /max_tokens\?: number \| null/);
  assert.match(types, /reasoning_effort\?: string \| null/);
});

test("obligation filters run before preview slicing and map review parts", async () => {
  const module = await import(
    "../web/app/obligations/obligation-filters.ts"
  );
  const filterClaims = (
    module as unknown as {
      filterClaims?: (
        claims: any[],
        view: "accepted" | "rejected",
        obligationType: string,
        affectedParty: string,
        filterText: string,
      ) => any[];
    }
  ).filterClaims;
  const resolveReviewPart = (
    module as unknown as {
      resolveReviewPart?: (
        documentNumber: string,
        grounding: any,
      ) => number | null;
    }
  ).resolveReviewPart;

  assert.equal(typeof filterClaims, "function");
  assert.equal(typeof resolveReviewPart, "function");
  if (!filterClaims || !resolveReviewPart) return;

  const claims = [
    {
      claim_id: "accepted-match",
      accepted: true,
      obligation_type: "reporting",
      affected_party: "Banks",
      summary: "Submit a quarterly report",
      quote: "Each bank must file the report.",
    },
    {
      claim_id: "accepted-other-party",
      accepted: true,
      obligation_type: "reporting",
      affected_party: "Insurers",
      summary: "Submit a quarterly report",
      quote: "Each insurer must file the report.",
    },
    {
      claim_id: "rejected-match",
      accepted: false,
      obligation_type: "reporting",
      affected_party: "Banks",
      summary: "Submit a quarterly report",
      quote: "Each bank must file the report.",
    },
  ];

  assert.deepEqual(
    filterClaims(claims, "accepted", "reporting", "Banks", "QUARTERLY")
      .map((claim) => claim.claim_id),
    ["accepted-match"],
  );
  assert.deepEqual(
    filterClaims(claims, "accepted", "", "", "MUST FILE")
      .map((claim) => claim.claim_id),
    ["accepted-match", "accepted-other-party"],
  );
  assert.equal(resolveReviewPart("31-CFR-223", null), 223);
  assert.equal(
    resolveReviewPart("2024-00594", {
      rules: [
        {
          document_number: "2024-00594",
          source_for_part: 285,
        },
      ],
    }),
    285,
  );
  assert.equal(resolveReviewPart("2024-99999", { rules: [] }), null);

  const source = read("app/obligations/ObligationsExplorer.tsx");
  assert.match(source, />\s*Obligation type\s*</);
  assert.match(source, />\s*Affected party\s*</);
  assert.match(source, />\s*Filter text\s*</);
  assert.match(source, /filteredClaims\.slice\(0,\s*CLAIM_PREVIEW_LIMIT\)/);
  assert.match(
    source,
    /\{displayedClaims\.length\} of \{filteredClaims\.length\} shown/,
  );
  assert.match(source, /<ReviewMemoPanel part=\{reviewPart\} compact \/>/);
});

test("review memo panels are silent without data and keep marker families balanced", () => {
  const source = read("app/components/ReviewMemoPanel.tsx");
  const authority = read("app/components/AuthoritySection.tsx");

  assert.match(source, /useLazyJson<ReviewMemoData>\("\/data\/memos\.json"/);
  assert.match(
    source,
    /if \(memoState\.status !== "ready"\) \{\s*return null;/,
  );
  assert.match(
    source,
    /Review signals — flagged for attorney review/,
  );
  assert.match(source, /Deference-reliance markers:/);
  assert.match(source, /Grounding-strength markers:/);
  assert.match(
    source,
    /Model-generated summary of the retrieval evidence — not a legal conclusion\./,
  );
  assert.match(source, /Narrative withheld by the memo gate\./);
  assert.match(
    source,
    /Full evidence on the Statutory authority page/,
  );
  assert.match(source, /href="\/authorities\/"/);
  assert.doesNotMatch(
    source,
    /\b(?:vulnerable|compliant|candidate|invalid|unnecessary)\b/i,
  );
  assert.match(authority, /<ReviewMemoPanel part=\{selectedPart\} \/>/);
});

test("evaluation uses metric cards and preserves the F1 interval caveat verbatim", () => {
  const core = read("app/components/EvalSection.tsx");
  const ogc01 = read("app/components/Ogc01EvalSection.tsx");
  const metricCard = read("app/components/ui/MetricCard.tsx");

  assert.ok(
    (ogc01.match(/<MetricCard/g) ?? []).length >= 5,
    "OGC-01 should render the five headline metric tiles",
  );
  for (const label of [
    "Authority-link F1",
    "Classification accuracy",
    "Marker precision",
    "Marker recall",
    "Draft conformance",
  ]) {
    assert.ok(ogc01.includes(`label="${label}"`), `missing ${label} tile`);
  }
  assert.match(metricCard, /note\?:\s*ReactNode/);
  assert.ok(
    core.includes(
      "Wilson interval not shown: F1 is not a binomial proportion.",
    ),
  );
});

test("search examples reuse local search and report only index-derived scope counts", () => {
  const source = read("app/components/SearchSection.tsx");
  const utils = read("app/components/search-utils.ts");
  const css = read("app/globals.css");

  for (const query of [
    "surety bond",
    "reporting requirement",
    "31 CFR 210",
    "skeleton",
  ]) {
    assert.ok(source.includes(`"${query}"`), `missing example query ${query}`);
  }
  assert.match(source, /runSearch\(exampleQuery\)/);
  assert.match(source, /countSearchUnitsByType\(index\)/);
  assert.match(utils, /index\.units\.reduce/);
  assert.match(source, /Indexed scope:/);
  assert.match(
    css,
    /\.search-results-region\s*\{[\s\S]*?min-height:/,
  );
});

test("browse headings are deduplicated and title-cased by a client-side formatter", async () => {
  const module = await import(
    "../web/app/components/search-utils.ts"
  );
  const formatPartHeading = (
    module as unknown as {
      formatPartHeading?: (part: number, heading: string) => string;
    }
  ).formatPartHeading;
  const source = read("app/components/BrowseSection.tsx");

  assert.equal(typeof formatPartHeading, "function");
  if (!formatPartHeading) return;

  assert.equal(
    formatPartHeading(
      50,
      "PART 50—TERRORISM RISK INSURANCE PROGRAM",
    ),
    "Terrorism Risk Insurance Program",
  );
  assert.equal(
    formatPartHeading(223, "Surety Companies"),
    "Surety Companies",
  );
  assert.match(source, /className="width-full text-left browse-part-button"/);
  assert.doesNotMatch(
    source.match(/className="width-full text-left browse-part-button"[\s\S]{0,220}/)?.[0] ?? "",
    /\bbase\b/,
  );
});

test("about prose has semantic structure, readable measure, and an isolated digest", () => {
  const source = read("app/components/AboutSection.tsx");
  const normalizedSource = source.replace(/\s+/g, " ");
  const css = read("app/globals.css");

  assert.doesNotMatch(source, /standalone/);
  assert.match(source, /const TraceabilityHeading = "h3";/);
  assert.match(
    source,
    /<h2 id="about" tabIndex=\{-1\}>[\s\S]*?About this demonstration[\s\S]*?<\/h2>/,
  );
  assert.ok(
    normalizedSource.includes(
      "RegLens-31 is an independent working mockup of one publicly documented Treasury AI use case:",
    ),
  );
  assert.ok(
    normalizedSource.includes(
      "Built from public primary sources only, it demonstrates what each of OGC-01’s stated outputs can look like when every claim must survive a verbatim, fail-closed provenance check.",
    ),
  );
  assert.match(
    source,
    /<h3 className="about-inventory-context-heading">[\s\S]*?Why this use case/,
  );
  assert.match(
    source,
    /<h4 id="about-inventory-heading">[\s\S]*?Treasury’s inventory entry for OGC-01/,
  );
  const contextHeading = source.indexOf(
    'className="about-inventory-context-heading"',
  );
  const inventoryHeading = source.indexOf(
    'id="about-inventory-heading"',
  );
  assert.ok(
    contextHeading >= 0 && contextHeading < inventoryHeading,
    "the inventory h4 should follow a real h3 section heading",
  );
  assert.match(
    source,
    /<TraceabilityHeading className="about-traceability-heading">[\s\S]*?Stated outputs and what this site demonstrates/,
  );
  assert.match(
    source,
    /<h3 id="about-governance-docs-heading">[\s\S]*?Methodology &amp; governance documents/,
  );
  for (const href of [
    "https://github.com/junecodetm/reglens-31#readme",
    "https://github.com/junecodetm/reglens-31/blob/main/docs/M25-21-CROSSWALK.md",
    "https://github.com/junecodetm/reglens-31/tree/main/governance",
    "https://github.com/junecodetm/reglens-31/blob/main/docs/EVALUATION.md",
  ]) {
    assert.ok(source.includes(`href="${href}"`), `missing governance link ${href}`);
  }
  assert.match(source, /<code className="about-inventory-digest">/);
  assert.match(css, /\.about-section > p[\s\S]*?max-width:\s*72ch;/);
  assert.match(
    css,
    /\.about-section > h3,\s*\.about-section > h4,/,
    "the demoted inventory h4 should retain the existing About heading style",
  );
  assert.match(css, /\.eval-details[\s\S]*?max-width:\s*72ch;/);
  assert.match(
    css,
    /\.about-traceability-heading[\s\S]*?border-top:\s*1px solid var\(--line\);/,
  );
});

test("overview cards are balanced and comparisons expose the required visible explanations", () => {
  const overview = read("app/OverviewContent.tsx");
  const diff = read("app/components/ui/DiffComparison.tsx");
  const css = read("app/globals.css");

  assert.ok(
    overview.includes(
      "Excerpt — the highlighted span is shown with surrounding context from the source document.",
    ),
  );
  assert.ok(
    diff.includes(
      "Underlined text appears only in the model's quote; struck-through text appears only in the closest source passage.",
    ),
  );
  assert.match(overview, /className="diff-comparison source-document"/);
  assert.match(
    css,
    /\.overview-cards\s*\{[\s\S]*?grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);/,
  );
});

test("neutral classifications and visible pass/fail words remain intact", () => {
  const authority = read("app/components/AuthoritySection.tsx");
  const drafts = read("app/components/DraftsSection.tsx");

  assert.match(
    authority,
    /CLASSIFICATION_CHIP_CLASS\s*=\s*[\s\S]*?"usa-tag bg-base-lighter text-ink text-normal"/,
  );
  assert.match(drafts, /return value \? "pass" : "fail"/);
  assert.match(drafts, /\{passFail\(value\)\}/);
});

test("the band definition constant matches the exported artifact byte-for-byte", () => {
  // The memo panel renders the constant; GroundingSection prefers the
  // exported grounding.json string. If they ever diverge, the two views
  // would print different definitions for the same bands.
  const source = read("app/components/GroundingSection.tsx");
  const match = source.match(
    /export const BAND_DEFINITION =\s*((?:"[^"]*"\s*;?\s*)+)/,
  );
  assert.ok(match, "BAND_DEFINITION not found in GroundingSection.tsx");
  const constant = Array.from(match[1].matchAll(/"([^"]*)"/g))
    .map((m) => m[1])
    .join("");
  const artifact = JSON.parse(
    readFileSync(join(WEB_ROOT, "public/data/grounding.json"), "utf8"),
  ) as { band_definition: string };
  assert.equal(constant, artifact.band_definition);
});
