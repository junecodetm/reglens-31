import assert from "node:assert/strict";
import test from "node:test";

import { buildAuthorityCrossReferences } from "../web/app/components/crossref-utils.ts";
import type { AuthorityData } from "../web/app/components/reglens-types.ts";

function resolved(
  uscTitle: number,
  uscSection: string,
): AuthorityData["parts"][number]["resolved"][number] {
  return {
    usc_title: uscTitle,
    usc_section: uscSection,
    identifier: `/us/usc/t${uscTitle}/s${uscSection}`,
    heading: "",
    status: null,
    text_sha256: "",
    classification: "silent",
    verb_quote: null,
    verb_start: null,
    verb_end: null,
    grant_spans: [],
    gate_rejected: false,
    rejection_reason: null,
  };
}

function part(
  partNumber: number,
  sections: Array<[number, string]>,
): AuthorityData["parts"][number] {
  return {
    part: partNumber,
    part_heading: "",
    ecfr_date: "",
    authority_text: "",
    part_text_sha256: "",
    authority_start: 0,
    authority_end: 0,
    ecfr_url: "",
    citations: [],
    resolved: sections.map(([title, section]) => resolved(title, section)),
    unresolved: [],
  };
}

test("cross references deduplicate parts, put shared authorities first, and sort each group", () => {
  const data = {
    parts: [
      part(501, [
        [31, "321"],
        [5, "301"],
        [31, "10"],
        [31, "2"],
      ]),
      part(50, [
        [5, "301"],
        [31, "321"],
        [5, "301"],
        [12, "391"],
      ]),
    ],
  } as AuthorityData;

  const references = buildAuthorityCrossReferences(data);

  assert.deepEqual(
    references.map(({ uscTitle, uscSection, parts }) => [
      uscTitle,
      uscSection,
      parts,
    ]),
    [
      [5, "301", [50, 501]],
      [31, "321", [50, 501]],
      [12, "391", [50]],
      [31, "2", [501]],
      [31, "10", [501]],
    ],
  );
});
