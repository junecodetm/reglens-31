export const GLOSSARY: Record<string, string> = {
  "provenance-gate":
    "A deterministic check that keeps an extracted claim only if its quoted text is an exact match, character for character, inside the government source document. Anything that doesn't match is rejected and counted, never silently dropped.",
  obligation:
    "A who-must-do-what statement — a requirement, prohibition, reporting duty, or similar — that a language model identified inside a published regulation.",
  "fail-closed":
    "If a check can't run, or can't confirm a match, the claim is rejected. Nothing is kept by default; everything must earn acceptance.",
  "verbatim-span":
    "The exact stretch of characters in the source document that a claim's quote was matched against, character for character.",
  "mandatory-discretionary-silent-unresolved":
    "How a cited statute's language was classified: mandatory (\"shall\"/\"must\"), discretionary (\"may\"), silent (no directive verb found), or unresolved (the citation couldn't be resolved to U.S. Code text at all).",
  "deference-reliance-marker":
    "A textual marker noting where a rule's preamble leans on judicial deference to the agency's own reading of a statute.",
  "grounding-strength-marker":
    "A textual marker noting where a rule's preamble ties its reasoning directly to the statute's own text. Reported with equal weight to deference-reliance markers, never as an opposing score.",
  "wilson-interval":
    "A confidence interval for a proportion (like precision or recall) that stays accurate even with a small sample or a rate near 0% or 100%.",
  "clustered-bootstrap":
    "A resampling method that accounts for provisions clustering within the same document, so the reported confidence interval isn't falsely narrow.",
  "cohens-kappa":
    "A statistic measuring how much two labeling passes agree, beyond what chance agreement alone would produce.",
  "provisional-label":
    "Machine-proposed, not yet reviewed by a human. Every metric on this page is provisional until adjudication completes.",
  nprm:
    "Notice of Proposed Rulemaking — the draft stage of a federal regulation, published for public comment before a final rule.",
  preamble:
    "The explanatory narrative that precedes a rule's regulatory text, stating its legal authority and reasoning.",
};

export function lookupGlossaryTerm(term: string): string | null {
  return Object.prototype.hasOwnProperty.call(GLOSSARY, term)
    ? GLOSSARY[term]
    : null;
}
