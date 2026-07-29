# PRODUCT.md — RegLens-31 front-end

## What this is
RegLens-31 is an independent working mockup of U.S. Treasury AI use case OGC-01
("Regulatory Reform Tool", Treasury public AI Use Case Inventory). It demonstrates
provenance-gated regulatory obligation extraction: every displayed claim carries a
verbatim source span verified by a deterministic, fail-closed substring check, and
claims that fail the check are counted and shown as rejections — never silently kept.
The deployed site is a pre-computed static export; nothing depends on a live backend,
an API key, or a network call.

## Audience
Primary: a U.S. Treasury reviewer evaluating this repository and site as a
job-application artifact for an IT Specialist (Artificial Intelligence) role —
technically literate, time-constrained, reading with a compliance/assurance eye.
Secondary: federal regulatory analysts and AI-governance practitioners assessing
whether the provenance/evaluation approach is credible.

## Usage mode
**Operate.** The visitor completes tasks: inspect a claim against its source span,
search the corpus, browse Title 31, trace authority citations, read evaluation
metrics. Routine transitions must be fast; nothing may feel decorative or promotional.

## Voice and framing constraints (binding — not preferences)
- Federal plain language. No marketing tone, no superlatives, no persuasion.
- Non-affiliation (31 U.S.C. §333): the disclaimer band appears on every page; no
  Treasury seals/symbols; nothing may imply endorsement.
- Neutrality (EXTEND-OGC01 §5): the site makes no deregulatory recommendations,
  nominates no rules or statutes for change, and draws no legal conclusions. Forbidden
  in our own voice: "vulnerability", "repeal candidate", "at risk", any legal-outcome
  prediction. No red/green semantic coloring of findings — presentation is two-sided
  and descriptive.
- Honesty protocol: evaluation numbers are labeled exactly
  "Provisional — machine-proposed labels, human-adjudicated: 0/N"; kappa is
  cross-model agreement, never described as human inter-annotator agreement; nothing
  is ever described as "hand-labeled".
- Every output is assistive, human-in-the-loop: "verify against the primary source."

## Product principles
1. Provenance first: the claim→verbatim-span link is the headline interaction;
   everything else supports it.
2. Show the failure counter: rejected claims are a feature, not an embarrassment.
3. Honest limits: provisional labels, coverage caveats, and "as of" staleness notes
   stay visible.
4. Zero dependence: works offline from the static export; degrades gracefully when a
   data file is missing (visible error notice, never a blank page).
5. Accessibility is a gate, not a goal: WCAG 2.1 AA / Section 508; axe zero
   violations; full keyboard operability.
