import assert from "node:assert/strict";
import test from "node:test";

import {
  assembleSkeleton,
  checkLiveDraft,
  countUnverifiedQuotes,
  MODEL_SUMMARY_SLOT,
  MODEL_SUPPLEMENTARY_SLOT,
  normalizeForGate,
  PLACEHOLDER,
  scanFabrication,
  verifyQuoteAgainst,
} from "../web/app/components/draft-live.ts";

// A minimal template shaped like the exporter's sentinel-slotted skeletons:
// all preamble captions in order, all analysis sections with placeholders.
const TEMPLATE = `DRAFT SKELETON

AGENCY: ${PLACEHOLDER}

ACTION: Notice of proposed rulemaking.

SUMMARY: [model-generated] ${MODEL_SUMMARY_SLOT}

DATES: Comments must be received on or before ${PLACEHOLDER}.

ADDRESSES: ${PLACEHOLDER}

FOR FURTHER INFORMATION CONTACT: ${PLACEHOLDER}

SUPPLEMENTARY INFORMATION:

   I. Background

   [model-generated] ${MODEL_SUPPLEMENTARY_SLOT}

   III. Regulatory Flexibility Act

      ${PLACEHOLDER}

   IV. Congressional Review Act

      ${PLACEHOLDER}

   V. Executive Order 12866 (Regulatory Planning and Review)

      ${PLACEHOLDER}

   VI. Paperwork Reduction Act

      ${PLACEHOLDER}

   VII. Unfunded Mandates Reform Act

      ${PLACEHOLDER}

   VIII. Executive Order 14192 (Regulatory Cost Offset Accounting)

      ${PLACEHOLDER}

List of Subjects in 31 CFR Part 223

   ${PLACEHOLDER}
`;

const PART_TEXT =
  "The Secretary shall administer the reporting requirements of this part.";
const CLEAN = "This part concerns sureties. The skeleton provides structure only.";

test("normalizeForGate mirrors the pipeline normalization", () => {
  // NFKC folds, whitespace runs collapse, ends trim.
  assert.equal(normalizeForGate("  a  b\nc  "), "a b c");
  assert.equal(normalizeForGate("ﬁle"), "file"); // U+FB01 ligature under NFKC
  assert.equal(normalizeForGate(""), "");
});

test("verifyQuoteAgainst accepts exact spans and rejects fabrications", () => {
  assert.ok(verifyQuoteAgainst(PART_TEXT, "Secretary   shall administer"));
  assert.ok(!verifyQuoteAgainst(PART_TEXT, "Secretary must administer"));
  assert.ok(!verifyQuoteAgainst(PART_TEXT, ""));
});

test("scanFabrication ports the conformance patterns", () => {
  assert.deepEqual(scanFabrication(CLEAN), []);
  assert.deepEqual(scanFabrication("It saves $5 million."), ["dollar-amount"]);
  assert.deepEqual(scanFabrication("Contact x@treasury.gov."), ["email"]);
  assert.deepEqual(
    scanFabrication("Effective January 3, 2027, always."),
    ["calendar-date"],
  );
});

test("countUnverifiedQuotes folds curly quotes and checks the source", () => {
  const real = `The statute provides “The Secretary shall administer the reporting requirements” here.`;
  assert.equal(countUnverifiedQuotes(real, PART_TEXT), 0);
  const fake = `The statute says "all persons must file annual reports" here.`;
  assert.equal(countUnverifiedQuotes(fake, PART_TEXT), 1);
});

test("assembleSkeleton splices both slots exactly once", () => {
  const assembled = assembleSkeleton(TEMPLATE, "S.", "B.");
  assert.ok(assembled.includes("SUMMARY: [model-generated] S."));
  assert.ok(assembled.includes("[model-generated] B."));
  assert.ok(!assembled.includes(MODEL_SUMMARY_SLOT));
  assert.throws(() => assembleSkeleton("no slots here", "S.", "B."));
});

test("checkLiveDraft passes a clean assembly and fails visibly on defects", () => {
  const clean = checkLiveDraft(assembleSkeleton(TEMPLATE, CLEAN, CLEAN), CLEAN, PART_TEXT);
  assert.ok(clean.passed, JSON.stringify(clean));

  const outOfOrder = checkLiveDraft(
    assembleSkeleton(TEMPLATE, CLEAN, CLEAN).replace("DATES:", "TIMING:"),
    CLEAN,
    PART_TEXT,
  );
  assert.ok(!outOfOrder.headings_in_order && !outOfOrder.passed);

  const filledStub = checkLiveDraft(
    assembleSkeleton(TEMPLATE, CLEAN, CLEAN).replace(
      `Congressional Review Act\n\n      ${PLACEHOLDER}`,
      "Congressional Review Act\n\n      No impact expected.",
    ),
    CLEAN,
    PART_TEXT,
  );
  assert.ok(!filledStub.placeholders_intact && !filledStub.passed);

  const fabricated = checkLiveDraft(
    assembleSkeleton(TEMPLATE, CLEAN, CLEAN),
    `${CLEAN} Assigned RIN 1505-AB12 by OIRA.`,
    PART_TEXT,
  );
  assert.ok(!fabricated.narrative_fabrication_clean && !fabricated.passed);
  assert.deepEqual(fabricated.fabrication_hits, ["rin"]);
});
