import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire, registerHooks } from "node:module";
import test from "node:test";

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

const { computeHighlightSegments } = await import(
  "../web/app/components/ui/HighlightedText.tsx"
);
const { ci, fmt } = await import(
  "../web/app/components/ui/metric-format.ts"
);
const { groupDocumentsByCategory } = await import(
  "../web/app/components/DocumentPicker.tsx"
);
const { nextTabIndex } = await import(
  "../web/app/components/ui/ViewTabs.tsx"
);
const { lookupGlossaryTerm } = await import(
  "../web/app/components/ui/glossary.ts"
);

test("highlight segmentation returns the complete text around an in-bounds span", () => {
  assert.deepEqual(
    computeHighlightSegments("0123456789", 2, 5),
    {
      status: "ready",
      segments: {
        before: "01",
        highlighted: "234",
        after: "56789",
      },
    },
  );
});

test("highlight segmentation reports missing offsets when no span is recorded", () => {
  assert.deepEqual(
    computeHighlightSegments("0123456789", null, null),
    {
      status: "missing-offsets",
      segments: null,
    },
  );
});

test("highlight segmentation reports invalid bounds for incomplete or out-of-bounds spans", () => {
  for (const [start, end] of [
    [null, 5],
    [2, null],
    [-1, 2],
    [4, 4],
    [5, 4],
    [2, 11],
  ] as const) {
    assert.deepEqual(
      computeHighlightSegments("0123456789", start, end),
      {
        status: "invalid-bounds",
        segments: null,
      },
    );
  }
});

test("highlight segmentation limits context to the requested character window", () => {
  assert.deepEqual(
    computeHighlightSegments("0123456789", 4, 6, 2),
    {
      status: "ready",
      segments: {
        before: "23",
        highlighted: "45",
        after: "67",
      },
    },
  );
});

test("highlight context windows clip cleanly at both text edges", () => {
  assert.deepEqual(
    computeHighlightSegments("0123456789", 1, 3, 5),
    {
      status: "ready",
      segments: {
        before: "0",
        highlighted: "12",
        after: "34567",
      },
    },
  );
  assert.deepEqual(
    computeHighlightSegments("0123456789", 7, 9, 5),
    {
      status: "ready",
      segments: {
        before: "23456",
        highlighted: "78",
        after: "9",
      },
    },
  );
});

test("highlight segmentation rejects invalid context window sizes", () => {
  for (const contextChars of [-1, 1.5, Number.NaN]) {
    assert.throws(
      () =>
        computeHighlightSegments(
          "0123456789",
          2,
          5,
          contextChars,
        ),
      RangeError,
    );
  }
});

test("fmt renders null and numeric metric values consistently", () => {
  assert.equal(fmt(null), "—");
  assert.equal(fmt(0), "0.000");
  assert.equal(fmt(1), "1.000");
  assert.equal(fmt(0.45678), "0.457");
});

test("ci renders nullable and numeric intervals consistently", () => {
  assert.equal(ci(null), null);
  assert.equal(ci([0, 1]), "[0.000, 1.000]");
  assert.equal(ci([0.1234, 0.9876]), "[0.123, 0.988]");
});

test("document grouping follows display order, sorts documents, and appends unknown categories", () => {
  const documents = [
    {
      category: "Uncatalogued material",
      document_number: "Z-200",
    },
    {
      category: "IRS & tax regulations",
      document_number: "2026-20000",
    },
    {
      category: "Title 31 — Code of Federal Regulations parts",
      document_number: "31-CFR-501",
    },
    {
      category: "Sanctions notices & general licenses (OFAC)",
      document_number: "2026-10000",
    },
    {
      category: "Sanctions notices & general licenses (OFAC)",
      document_number: "2026-09000",
    },
    {
      category: "Title 31 — Code of Federal Regulations parts",
      document_number: "31-CFR-223",
    },
    {
      category: "Archived material",
      document_number: "A-100",
    },
    {
      category: "Archived material",
      document_number: "A-050",
    },
  ] as any;

  const groups = groupDocumentsByCategory(documents);

  assert.deepEqual(
    groups.map((group) => ({
      category: group.category,
      documentNumbers: group.documents.map(
        (document) => document.document_number,
      ),
    })),
    [
      {
        category: "Title 31 — Code of Federal Regulations parts",
        documentNumbers: ["31-CFR-223", "31-CFR-501"],
      },
      {
        category: "Sanctions notices & general licenses (OFAC)",
        documentNumbers: ["2026-09000", "2026-10000"],
      },
      {
        category: "IRS & tax regulations",
        documentNumbers: ["2026-20000"],
      },
      {
        category: "Archived material",
        documentNumbers: ["A-050", "A-100"],
      },
      {
        category: "Uncatalogued material",
        documentNumbers: ["Z-200"],
      },
    ],
  );
});

test("tab keyboard navigation wraps and maps vertical arrows to horizontal movement", () => {
  const cases = [
    [2, "ArrowRight", 3, 0],
    [0, "ArrowLeft", 3, 2],
    [2, "ArrowDown", 3, 0],
    [0, "ArrowUp", 3, 2],
    [1, "Home", 3, 0],
    [1, "End", 3, 2],
  ] as const;

  for (const [currentIndex, key, tabCount, expected] of cases) {
    assert.equal(
      nextTabIndex(currentIndex, key, tabCount),
      expected,
      `${key} from index ${currentIndex}`,
    );
  }
});

test("glossary lookup returns known definitions and null for unknown terms", () => {
  assert.equal(
    lookupGlossaryTerm("provenance-gate"),
    "A deterministic check that keeps an extracted claim only if its quoted text is an exact match, character for character, inside the government source document. Anything that doesn't match is rejected and counted, never silently dropped.",
  );
  assert.equal(lookupGlossaryTerm("not-in-the-glossary"), null);
});
