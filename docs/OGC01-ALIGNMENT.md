# OGC-01 Alignment — What This Repo Demonstrates, and What It Deliberately Does Not Do

> Intended reader: a skeptical attorney. The Limitations section below is the
> most important section in this repository, and the Framing Constraints
> section is the standing brief for the blocking neutrality review.

## What OGC-01 is

The public Treasury AI Use Case Inventory lists **OGC-01, "Regulatory Reform
Tool"** (Office of General Counsel; Generative AI; High-impact; Pre-Deployment).
Verbatim from the published inventory record:

> "Prepares draft proposed and final regulations; reviews statutes for potential
> deregulatory actions. […] The tool seeks to identify statutes that are not
> statutorily required or that are inconsistent with Looper Bright [sic];
> generates draft proposed and final rules"

("Looper Bright" is a typo in the official record for *Loper Bright Enterprises
v. Raimondo*, 603 U.S. 369 (2024); it is spelled correctly everywhere in this
repository. The typo is noted once, here, as evidence the primary source was
read.)

## The legal environment this tool serves

*Loper Bright*, *Corner Post, Inc. v. Board of Governors*, Executive Order
14219, Executive Order 14192, and the April 2025 Presidential memorandum on
repeal of unlawful regulations are cited in this repository solely as the legal
environment OGC-01's own record frames — the context a regulatory-reform tool
must operate in. Nothing here endorses, criticizes, or characterizes any of
them.

## What this repository demonstrates

1. **Statutory authority linker.** For each in-scope CFR part, the authority
   citation is parsed from the eCFR (exact span preserved), each cited U.S.C.
   section is resolved against a pinned OLRC USLM release point, and the
   operative grant is classified {mandatory, discretionary, silent, unresolved}
   with the verbatim statutory verb phrase, verified by a deterministic
   exact-substring gate. Classification is **deterministic pattern retrieval —
   not model inference**: the pattern table in `reglens/authority/classify.py`
   is the entire classifier, it is published, and its accuracy is measured
   against proposed gold labels and reported with confidence intervals.
2. **Two-sided grounding signal.** Exact, gate-verified marker spans from
   Federal Register document text, in two families of equal weight —
   deference-reliance AND grounding-strength — plus two per-rule facts (whether
   the rule predates *Loper Bright*; whether the text cites *Chevron*). Bands
   report textual-marker density only, with the definition printed beside them.
3. **Draft rule skeletons, parameterized.** Document Drafting Handbook–
   conformant skeletons for every in-scope part in both NPRM and final-rule
   form, whose structure is deterministic, whose only model-generated text is
   a labeled narrative opening, and whose every required analysis renders as a
   visible `[PLACEHOLDER — attorney to complete]` block. A structural
   conformance checker (heading order, amendatory-instruction grammar, intact
   placeholders, fabrication scan, zero unverifiable quotes) rejects — does
   not caveat — any failing draft. The /drafts page additionally accepts
   parameters (part, rule type, an optional policy objective) and can generate
   the narrative opening live through a same-origin endpoint; live output is
   checked by an in-browser subset of the same gate, labeled as such, and
   falls back to the committed, fully gated drafts on any failure.
4. **Per-part review memoranda.** For each part, the assembled retrieval
   evidence — authority classifications and both marker families — plus a
   short model-written narrative that restates that evidence. The narrative is
   gated deterministically (no numerals, no quotations, no fabrication
   patterns, both marker families named) and labeled model-generated; every
   number shown comes from the deterministic evidence, never from the model.

## Framing constraints — non-negotiable

This repo analyzes a politically contested subject and will be read by
attorneys. Every one of these is a hard requirement, not a preference, and the
`neutrality-reviewer` agent's sole brief is compliance with them:

1. **No legal conclusions, ever.** Output is retrieval and structure. The tool
   flags text for attorney review; it does not evaluate legality.
2. **Cite the operative legal context neutrally.** *Loper Bright*, *Corner
   Post*, E.O. 14219, E.O. 14192, and the April 2025 repeal memorandum are
   cited as **the legal environment the tool must serve** — the same way
   OGC-01's own record frames it. No endorsement, no criticism, no adjectives.
3. **Two-sided by construction.** Grounding-strength markers ship in the same
   release as deference-reliance markers, in the same view, with equal visual
   weight.
4. **Disclaimers, above the fold, on every page:** not affiliated with, endorsed
   by, or produced for the U.S. Department of the Treasury or any agency
   (31 U.S.C. §333); not legal advice; no attorney-client relationship;
   model-generated fields visibly marked as such.
5. **This document states plainly** what OGC-01 is (citing the public
   inventory), what this repo demonstrates, and — explicitly — what it
   deliberately does not do.
6. **Never claim any capability the eval does not support.** Precision of
   0.434 is reported as 0.434.

Also categorically out of scope: case-outcome prediction of any kind,
cost-benefit estimation with invented numbers, any ranked "repeal candidates"
list, and scope expansion into 31 CFR Ch. V (substantive sanctions programs)
or Ch. X (BSA/AML).

## Limitations — what this tool deliberately does not do

1. **It makes no legal conclusions.** Output is retrieval and structure. It
   flags text for attorney review; it does not evaluate the legality,
   validity, or vulnerability of any regulation, and no output should be read
   as such.
2. **It predicts nothing.** There is no judicial-outcome metric anywhere in
   this repository, and none will be added: such a metric would be
   unfalsifiable. Marker densities describe phrase frequency in published
   text — nothing else.
3. **It ranks nothing for repeal.** There is no "repeal candidate" list, no
   risk score, no red/green treatment, and the word "vulnerability" does not
   appear in shipped UI copy.
4. **"Silent" is a pattern-table result, not a finding of absent authority.**
   A section classified silent means none of the published grant patterns
   matched. Statutes grant rulemaking authority in ways a finite pattern table
   will miss (and occasionally over-match); the classifier's measured accuracy,
   with intervals, is on the evaluation page. The edge decision that "under
   regulations prescribed by the Secretary" presupposes rather than grants
   authority is documented in the classifier and seeded in the gold set.
5. **The West Virginia v. EPA marker is analytic, not literal.** "Reliance on
   general authority to reach a major question" cannot be found by exact
   phrase search; only the literal families listed in
   `reglens/grounding/markers.py` are searched. Absence of a marker is not
   evidence of anything.
6. **Note, Public Law, and Executive Order citations are not classified.**
   E.g. "15 U.S.C. 6701 note" (TRIA) resolves to statutory notes, not the
   codified section; these citations are displayed as a coverage category and
   never quoted as codified section text.
7. **Scope is five fiscal/debt-management parts of 31 CFR** (50, 223, 285,
   356, 501) at pinned snapshot dates. Nothing here touches sanctions programs
   substantively (Ch. V beyond part 501's procedures), BSA/AML (Ch. X), or any
   restricted data.
8. **Evaluation labels are provisional.** Gold labels are machine-proposed and
   carry the label "Provisional — machine-proposed labels, human-adjudicated:
   N/M" until human adjudication; reported kappa is CROSS-MODEL agreement
   between two different frontier models, not human inter-annotator agreement.
   Metrics are reported as measured — including the unflattering ones.
9. **The authority-linking evaluation is a census, not a sample.** All citation
   pairs from the five in-scope parts are evaluated; one part (501) dominates
   the pair count, and the clustered bootstrap runs over only five part-level
   clusters — both facts are printed beside the intervals.
10. **Draft skeletons contain no substance.** The generator produces structure;
    the human produces substance. A skeleton is not a proposed rule, does not
    name an issuing agency, and invents no docket, RIN, date, cost, or contact
    — a fabrication scan rejects any draft where the model tries.
11. **Quote-check normalization extension.** The draft checker folds curly
    quotes to straight quotes before quote detection and verification (the
    core provenance normalization is NFKC + whitespace and does not fold
    them). This is the only normalization difference, documented here and in
    `reglens/draft/conformance.py`.
12. **Live draft narratives pass a subset of the gate.** The in-browser checks
    (`web/app/components/draft-live.ts`) cover heading order, analysis-section
    and placeholder integrity, the fabrication scan, and verbatim quote
    verification against the shipped part text; the full build-time gate —
    including set-out verification against cited U.S.C. section text — runs
    only on the committed drafts. The UI labels live output as
    subset-checked and never presents it as a fully gated draft.
13. **Not affiliated with the U.S. Department of the Treasury** or any agency
    (31 U.S.C. §333); not legal advice; no attorney-client relationship. This
    is an independent technical demonstration built solely from public data.

## Prior art noted

RegData's restriction-counting methodology (Al-Ubaydli & McLaughlin) is prior
art for counting regulatory obligation markers at scale. This project does not
ingest QuantGov/RegData data; the approaches differ in that every count here is
backed by a verbatim, gate-verified span in the primary source.
