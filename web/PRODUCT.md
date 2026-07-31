# RegLens-31 front-end product requirements

## What this is
RegLens-31 is an independent working mockup of U.S. Treasury AI use case OGC-01
("Regulatory Reform Tool", Treasury public AI Use Case Inventory). It demonstrates
provenance-gated regulatory obligation extraction: every displayed claim carries a
verbatim source span verified by a deterministic, fail-closed substring check, and
claims that fail the check are counted and shown as rejections — never silently kept.
The deployed site is a pre-computed static export. Core pages and the read API
do not depend on a live backend, API key, or network call. Live drafting is an
optional same-origin enhancement with committed-draft fallback.

## Audience
Primary users are technically literate federal reviewers assessing the system's
evidence, limitations, and controls. Federal regulatory analysts and
AI-governance practitioners are secondary users.

## Usage mode
The interface supports task-oriented review: inspect a claim against its source
span, search the corpus, browse Title 31, trace authority citations, and read
evaluation metrics. Routine transitions must be fast and non-decorative.

## Voice and framing constraints (binding — not preferences)
- Federal plain language. No marketing tone, no superlatives, no persuasion.
- Non-affiliation (31 U.S.C. §333): the disclaimer band appears on every page; no
  Treasury seals/symbols; nothing may imply endorsement.
- Neutrality ([framing constraints](../docs/OGC01-ALIGNMENT.md#framing-constraints--non-negotiable)):
  the site makes no deregulatory recommendations, nominates no rules or statutes for
  change, and draws no legal conclusions. Forbidden in our own voice: "vulnerability",
  "repeal candidate", "at risk", any legal-outcome prediction. No red/green semantic
  coloring of findings — presentation is two-sided and descriptive.
- Honesty protocol: evaluation numbers are labeled exactly
  "Provisional — machine-proposed labels, human-adjudicated: N/M"; kappa is
  CROSS-MODEL agreement between two different frontier models, never human
  inter-annotator agreement; labels are not described as human-produced before
  adjudication.
- Every output is assistive, human-in-the-loop: "verify against the primary source."

## Product principles
1. The claim→verbatim-span link is the primary interaction.
2. Expose rejection counts and supporting evidence.
3. Provisional labels, coverage caveats, and "as of" staleness notes remain visible.
4. The static export operates offline and displays an error notice when a data file is
   missing.
5. WCAG 2.1 AA, Section 508, zero axe violations, and full keyboard operability are
   release requirements.
