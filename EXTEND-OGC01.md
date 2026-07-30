# EXTEND-OGC01 — Authority, Grounding, and Drafting

Sequel to BUILD.md. RegLens-31 is COMPLETE per docs/PROGRESS.md. This spec adds the
three capabilities that map to Treasury AI Use Case **OGC-01 "Regulatory Reform Tool"**
(Office of General Counsel; Generative AI; **High-impact**; Pre-Deployment).

Read CLAUDE.md and BUILD.md first. Every operating rule in BUILD.md §1 (context
discipline, token discipline, subagent policy) and §6 (quality bar) carries over
unchanged and is not restated here. This file governs WHAT to build and the
non-negotiable framing constraints.

## 0. WHAT OGC-01 ACTUALLY ASKS FOR

Verbatim from the published Treasury AI Use Case Inventory:

> Prepares draft proposed and final regulations; reviews statutes for potential
> deregulatory actions. […] The tool seeks to identify statutes that are not
> statutorily required or that are inconsistent with Looper Bright [sic]; generates
> draft proposed and final rules

("Looper Bright" is a typo in the official record for *Loper Bright Enterprises v.
Raimondo*, 603 U.S. 369 (2024). Spell it correctly everywhere in this repo. You may
note the source typo once, in docs, as evidence the primary source was read.)

Decomposed into three buildable capabilities:

1. **"not statutorily required"** → regulation → authority-citation → U.S.C. mapping,
   with the operative statutory verb classified and quoted.
2. **"inconsistent with Loper Bright"** → retrieval of deference-reliance markers from
   Federal Register preamble text. **A retrieval task, never a prediction task.**
3. **"generates draft proposed and final rules"** → Document Drafting Handbook–conformant
   NPRM/final-rule skeletons with well-formed amendatory instructions.

## 1. PREFLIGHT — one message, then STOP

Ask everything at once as a numbered list, then wait. After I answer, run unattended.
Verify every answer programmatically; do not trust my answers.

Must include at minimum:
- Current repo state: branch, working tree clean, CI green? (`gh run list`, `git status`)
- **Was the Cloudflare API token rolled?** docs/PROGRESS.md flagged it as action #1. If not,
  stop and make me do it before any deploy step.
- Ollama model still pulled and tag unchanged from the recorded pin? (`ollama list`)
- Scope confirmation: keep the existing 31 CFR parts (50/223/285/356/501) or extend?
  **Recommend keeping.** Corrected 2026-07-30 — the earlier description of these as
  "fiscal/debt-management/government-securities parts" was wrong for two of the five, and
  a Treasury reviewer would catch it. They span three chapters: Part 50 is the Terrorism
  Risk Insurance Program (Ch. I, Departmental Offices); 223 (surety companies), 285 (debt
  collection) and 356 (marketable Treasury securities) are Bureau of the Fiscal Service
  parts (Ch. II); and Part 501 is the OFAC Reporting, Procedures and Penalties Regulations
  (Ch. V). The real selection principle is drafting-style variety across substantively
  real, politically inert parts — not a single subject-matter family.
  Part 501 is admissible despite being Ch. V because it is **procedural** — reporting,
  recordkeeping, licensing and penalty procedure — not a substantive designation program.
  What §5 rules out is proposing changes to sanctions *programs* or BSA/AML (Ch. X)
  substance; extracting verbatim procedural obligations makes no designation or screening
  determination. Canonical scope now lives in `reglens/corpus.py`.
- The eCFR snapshot date to pin, and the OLRC U.S. Code release point to pin.
- Confirm the provisional-labeling protocol (BUILD.md §4) stays in force. It does.

## 2. DATA SOURCES — free, keyless, snapshot-at-build-time

The zero-cost invariant from BUILD.md §2.7 holds absolutely. Extend the existing
zero-cost allow-list checker to cover exactly these and nothing else:

| Source | Endpoint / location | Auth |
|---|---|---|
| eCFR | `https://www.ecfr.gov` — versioner API (`/api/versioner/v1/...`: `full`, `structure`, `versions`, `ancestry`) | **none** |
| Federal Register | `https://www.federalregister.gov/api/v1/` — `documents.json`, `documents/{doc_number}.json`; follow `full_text_xml_url` / `raw_text_url` | **none** |
| U.S. Code (USLM XML) | `https://uscode.house.gov/download/download.shtml` — pinned release point ZIP | none |
| GovInfo bulk data | `https://www.govinfo.gov/bulkdata/` (CFR, FR, USCODE) | none for bulk |
| reginfo.gov | Unified Agenda; E.O. 14192 accounting workbooks | none |
| Document Drafting Handbook | `https://www.archives.gov/federal-register/write/handbook` (Aug 2018 ed., rev. 2.2) | none |

Verify parameter shapes against `https://www.ecfr.gov/developers/documentation/api/v1`
and `https://www.federalregister.gov/developers/documentation/api/v1` before coding.
Do not trust endpoint shapes written from memory — including the ones in this table.

**Snapshot everything at build time** into `data/raw/<sha256>/` with `manifest.json`,
exactly as the existing ingest does. `just demo` must still run fully offline on a
clean clone (BUILD.md §2.3). No network at runtime, ever.

**Explicitly forbidden as dependencies:**
- **CourtListener API.** As of 2026-05-07 the free tier is 5 req/min, 50/hr, 125/day.
  It cannot support this pipeline and a membership breaks the zero-cost invariant.
  The `eyecite` library (open source, local, no service call) is permitted for citation
  *parsing*; citation *lookup* is out of scope.
- **QuantGov / RegData datasets.** Cite RegData's restriction-counting methodology as
  prior art in docs. Do not ingest their data. It buys nothing technically and imports
  an institutional association into a politically sensitive project.
- Anything requiring an api.data.gov key. Free, but a CI secret and a runtime dependency
  for no gain. Prefer bulk downloads.

## 3. BUILD ORDER — vertical slices, always shippable

Commit and push after each step. Never leave the repo broken. Reuse the existing
provenance gate module; do not fork or reimplement it.

### Stage 1 — Statutory Authority Linker (highest leverage; ship even if nothing else does)

1. Parse the **authority citation** for each in-scope CFR part from eCFR XML
   (e.g. `Authority: 31 U.S.C. 3101 et seq.`). Preserve the exact citation span.
2. Resolve each cited section against pinned OLRC USLM XML. Record the U.S.C. section
   text and its exact span.
3. Classify the **operative grant** into exactly one of:
   - `mandatory` — statute directs issuance ("shall prescribe/issue regulations")
   - `discretionary` — statute permits ("may prescribe/issue")
   - `silent` — cited section contains no rulemaking grant
   - `unresolved` — citation could not be resolved to a section; **fail closed, do not guess**
4. **Every classification must carry the verbatim operative verb phrase, gate-verified
   against the statutory source.** A classification whose quoted span fails the exact-substring
   check is rejected, not downgraded. Surface the rejection in the existing counter.
5. UI: CFR part → authority citation (highlighted in source) → U.S.C. section (highlighted
   in source) → classification chip + the quoted verb. Reuse the existing click-to-span pattern.

This is the whole ballgame. It implements "identify statutes that are not statutorily
required" while making **zero legal conclusions** — it surfaces the statutory verb and
lets a lawyer judge.

### Stage 2 — Statutory Grounding Signal (two-sided, retrieval-only)

Not a "vulnerability score." A **two-sided grounding signal**, because a tool that only
searches for weakness is biased by construction and an attorney will say so.

1. For each in-scope rule, pull the Federal Register preamble via the FR API and snapshot it.
2. Extract, as **exact gate-verified spans**, two marker families:
   - **Deference-reliance markers:** citations to *Chevron*; "silent or ambiguous";
     "permissible construction"; "reasonable interpretation"; reliance on general or
     "necessary and appropriate" authority to reach a question of major economic or
     political significance (cf. *West Virginia v. EPA*).
   - **Grounding-strength markers:** express statutory delegation; a specific statutory
     mandate to regulate; explicit statutory definitions the rule tracks; Congressional
     ratification language.
3. Report **marker counts and their spans**. If you emit a band (`low`/`moderate`/`elevated`),
   it must be labeled precisely as *textual-marker density*, defined in the UI, and
   accompanied by both marker families. It is **not** a prediction of judicial outcome.
4. Also record, per rule, whether it predates *Loper Bright* (2024-06-28) and whether the
   preamble cites *Chevron* at all — both are facts, not judgments.

**Absolutely forbidden output:** any statement, ranking, label, sort order, or visual
treatment that says or implies a regulation should be repealed, is unlawful, is likely to
be struck down, or is a "repeal candidate." No red/green. No "at risk" framing. The word
"vulnerability" does not appear in shipped UI copy.

### Stage 3 — Draft Rule Skeleton Generator

1. Generate a **Document Drafting Handbook–conformant** proposed-rule or final-rule
   skeleton: preamble headings in required order (AGENCY, ACTION, SUMMARY, DATES,
   ADDRESSES, FOR FURTHER INFORMATION CONTACT, SUPPLEMENTARY INFORMATION), authority
   citation, and **well-formed amendatory instructions** (numbered, imperative,
   part/section-scoped).
2. Stub — do not fabricate — the required analyses: Regulatory Flexibility Act,
   Congressional Review Act submission, E.O. 12866/OIRA, Paperwork Reduction Act, UMRA,
   and an E.O. 14192 offset-accounting section using the reginfo.gov workbook fields.
3. **Every stub renders as a visible `[PLACEHOLDER — attorney to complete]` block.**
   The generator produces structure; the human produces substance. A skeleton that
   silently invents a cost estimate, a docket number, an RIN, or a contact is a defect.
4. Any statutory or regulatory text quoted inside a generated draft passes the provenance
   gate. Unverifiable quote → the draft is rejected, not published with a caveat.
5. Add a structural conformance checker: required headings present, amendatory instructions
   parse, no placeholder silently filled, zero unverified quotes. This is the only honest
   "accuracy" metric available for generation — report it as a checklist pass rate.

### Stage 4 — Governance crosswalk (small, high-return)

Write `docs/M25-21-CROSSWALK.md`: a table mapping each minimum risk-management practice
for high-impact AI in OMB M-25-21 (issued 2025-04-03) §4(b) — pre-deployment testing,
AI impact assessment, ongoing monitoring, human training, human oversight with a fail-safe,
remedy/appeal, feedback — to the concrete artifact in this repo that demonstrates it.

Also map the anti-confabulation posture to NIST AI 600-1 (Generative AI Profile) risk
categories **Confabulation** and **Information Integrity**.

Verify M-25-21's deadline structure against the memo PDF before writing dates. Known:
the 365-day mark (≈2026-04-03) applied to high-impact AI **already in operations** —
non-compliant systems came out of operations or took a CAIO waiver. Pre-deployment
use cases are gated, not shut down. Do not restate any secondary source's deadline
without checking it against the memo text.

## 4. EVALUATION — extend the existing harness, keep the labeling protocol

BUILD.md §4 governs. Subagents propose; they do not create ground truth. Everything
ships labeled *"Provisional — machine-proposed labels, human-adjudicated: 0/N."*

- **Authority linking:** gold set of 150–250 (CFR part → U.S.C. section) pairs. Report
  link P/R/F1 and classification accuracy over {mandatory, discretionary, silent}, with
  95% Wilson intervals and clustered bootstrap CIs by CFR part. Reuse the existing
  design-effect machinery. Report `unresolved` rate separately — it is a coverage fact,
  not an error.
- **Grounding markers:** scored as **retrieval** — did we find marker spans that are
  actually in the preamble? Exact-span match. Report the gate rejection rate as a
  first-class metric alongside P/R. **Do not report any metric of the form "predicted
  judicial outcome."** It is unfalsifiable and reporting it would be disqualifying.
- **Draft skeletons:** structural conformance pass rate + unverified-quote count (target: 0).
- Append new gold records to `docs/ADJUDICATE.md` in the existing numbered-worklist format.
  Wire the adjudicated counter so it restates from the JSONL automatically.
- Arm the CI regression gate at each new baseline minus 0.05, matching existing practice.

## 5. FRAMING CONSTRAINTS — non-negotiable, and the part most likely to sink this

This repo analyzes a politically contested subject. It will be read by attorneys. Every
one of these is a hard requirement, not a preference.

1. **No legal conclusions, ever.** Output is retrieval and structure. The tool flags text
   for attorney review; it does not evaluate legality.
2. **Cite the operative legal context neutrally.** *Loper Bright*, *Corner Post*,
   E.O. 14219, E.O. 14192, and the April 2025 repeal memorandum are cited as **the legal
   environment the tool must serve** — the same way OGC-01's own record frames it. No
   endorsement, no criticism, no adjectives.
3. **Two-sided by construction.** Grounding-strength markers ship in the same release as
   deference-reliance markers, in the same view, with equal visual weight.
4. **Disclaimers, above the fold, on every page:**
   - Not affiliated with, endorsed by, or produced for the U.S. Department of the Treasury
     or any agency (31 U.S.C. §333).
   - Not legal advice. No attorney-client relationship. Independent technical demonstration.
   - Model-generated fields visibly marked as such, as they already are.
5. **`docs/OGC01-ALIGNMENT.md`** states plainly: what OGC-01 is (citing the public
   inventory), what this repo demonstrates, and — explicitly — **what it deliberately does
   not do**. The limitations section is the most important section in the repo. Write it
   as if the reader is a skeptical GS-15 attorney, because that is the intended reader.
6. Never claim any capability the eval does not support. Precision of 0.434 is reported
   as 0.434.

## 6. DE-SCOPED — do not build, do not propose

Already sanctioned as out of scope in BUILD.md and still out: OFAC 50% ownership graph,
OSCAL component definitions, SLSA L3, Groq escalation, Inspect AI wrapper, commit signing.

Newly forbidden: CourtListener runtime dependency; QuantGov data ingestion; case-outcome
prediction of any kind; cost-benefit estimation with invented numbers; any ranked
"repeal candidates" list; scope expansion into 31 CFR Ch. V or Ch. X.

If you fall behind, de-scope in this order: Stage 3 → Stage 2 → Stage 4. **Never de-scope
Stage 1, the provenance gate, the eval labeling protocol, the disclaimers, or a11y.**

## 7. DEFINITION OF DONE

1. All BUILD.md §2 criteria still hold. Nothing regressed.
2. Stage 1 live on the deployed URL, gate-verified end to end, with a passing test proving
   an unresolvable authority citation fails closed rather than being guessed.
3. Stages 2–4 shipped or explicitly recorded as de-scoped with the reason.
4. Extended zero-cost allow-list checker passes; no new domains beyond §2; no new secrets.
5. `just demo` still runs fully offline on a clean clone.
6. New eval metrics render with Wilson CIs, bootstrap CIs, and the provisional label.
7. Playwright audit (BUILD.md §5) re-run to **two consecutive fully clean passes** locally
   plus a clean pass on the deployed URL, including the new views at 1440/768/375.
8. axe-core: zero serious/critical violations. Disclaimers visible without scrolling.
9. All subagent reviewers re-run in parallel; every finding fixed. Add a
   `neutrality-reviewer` subagent whose sole brief is §5 compliance — it reads shipped UI
   copy and docs and returns a verdict plus violations. Its findings are blocking.
10. docs/PROGRESS.md updated: what was built, what was de-scoped and why, adjudication
    status, exact next actions.

## 8. FINISH

Report in under 200 words: live URL, repo URL, new eval numbers with CIs and their
provisional label, structural conformance rate, what was de-scoped, the neutrality
reviewer's verdict, and anything needing my judgment.

Begin with §1. Ask everything at once, then run to completion.
