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
  const claimsPane = read("app/components/ClaimsPane.tsx");
  const sourcePane = read("app/components/SourcePane.tsx");
  const css = read("app/globals.css");

  for (const source of [explorer, claimsPane]) {
    assert.match(source, /CLAIM_PREVIEW_LIMIT\s*=\s*25/);
    assert.match(source, /Show all \$\{/);
    assert.match(source, /\.slice\(0,\s*CLAIM_PREVIEW_LIMIT\)/);
    assert.match(source, /aria-expanded=/);
    assert.match(source, /aria-controls=/);
    assert.match(source, /Show fewer/);
  }
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
  const css = read("app/globals.css");

  assert.match(
    source,
    /<h3 id="about-inventory-heading">[\s\S]*?Treasury’s inventory entry for OGC-01/,
  );
  const contextHeading = source.indexOf(
    'className="about-inventory-context-heading"',
  );
  const inventoryHeading = source.indexOf(
    'id="about-inventory-heading"',
  );
  assert.ok(
    contextHeading >= 0 && contextHeading < inventoryHeading,
    "the inventory h3 should follow a real h2 section heading",
  );
  assert.ok(
    source.includes("Stated outputs and what this site demonstrates"),
  );
  assert.match(source, /<code className="about-inventory-digest">/);
  assert.match(css, /\.about-section > p[\s\S]*?max-width:\s*72ch;/);
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
