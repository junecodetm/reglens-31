# PROGRESS — RegLens-31

> **Status: COMPLETE — no remaining work.** Base build 2026-07-28 per BUILD.md;
> OGC-01 extension 2026-07-28/29 per EXTEND-OGC01.md, single pass.
> Live: **https://reglens-31.pages.dev** · Repo: **https://github.com/junecodetm/reglens-31**

## Base build (BUILD.md — unchanged, nothing regressed)

- Allow-list-enforced ingest → local extraction (qwen3:8b, temp 0, JSON-schema) →
  **fail-closed provenance gate** → SQLite/DuckDB/Parquet → static export.
  25 documents, 950 accepted / 163 rejected claims; fabricated-quote rejection
  proven by tests and visible in the UI.
- Core eval (251 provisions): P=0.434 (Wilson 0.329–0.546), R=0.647
  (Wilson 0.510–0.764), F1=0.520; fidelity 1.000; cross-model κ=0.938;
  n_eff≈122. Label: *Provisional — machine-proposed labels, human-adjudicated: 0/251.*

## OGC-01 extension (EXTEND-OGC01.md) — what was built (all verified)

- **Stage 1 — Statutory authority linker** (`reglens/authority/` + `reglens/ingest/uscode.py`):
  authority lines parsed from eCFR XML at pinned date 2026-07-27 with exact
  gate-verified spans; typed citations (usc-section / usc-note / Pub. L. / E.O.);
  every cited section resolved against OLRC USLM release point **PL 119-102**
  (13 title zips cached gitignored; only cited-section fragments snapshotted);
  deterministic operative-grant classifier (published pattern table, mandatory >
  discretionary > silent precedence, negation guards) with every verb phrase
  provenance-gate-verified. **Census: 150 section citations — 116 resolved
  (15 mandatory / 16 discretionary / 85 silent), 34 unresolved (CISADA-range
  codification gaps, fail-closed), 4 non-section, 0 gate rejections.**
  Unresolvable citations fail closed — proven by test (DoD #2).
- **Stage 2 — Two-sided grounding signal** (`reglens/grounding/`): deterministic
  literal marker retrieval over 24 FR documents (incl. the four per-part source
  preambles; part 223 recorded as "preamble unavailable" coverage fact) —
  8 deference-reliance / 35 grounding-strength spans, 0 gate rejections; per-rule
  facts (predates *Loper Bright*; cites *Chevron*); bands are textual-marker
  density only, definition displayed verbatim in the UI.
- **Stage 3 — Draft rule skeletons** (`reglens/draft/`): DDH (Aug 2018 rev. 2.2,
  snapshotted) template with placeholders for every required analysis; model
  narrative (labeled) is the only generative text; fabrication scan + quote gate +
  set-out verification; **6/6 drafts pass conformance (rate 1.00, 0 unverified quotes)**.
- **Stage 4 — Governance**: docs/M25-21-CROSSWALK.md (practices + deadline text
  verified against the memo PDF) and docs/OGC01-ALIGNMENT.md (limitations-first,
  written for a skeptical attorney; notes the "Looper Bright" inventory typo once).
- **Eval** (`reglens/eval/ogc01.py`, provisional — 0/306 human-adjudicated,
  two frozen cross-model proposal passes fable-5/sonnet-5):
  link P=1.000 R=1.000 F1=1.000 (150-pair census; both blind enumerations matched
  the parser; κ=1.0); classification accuracy **0.884** (99/112; Wilson
  0.811–0.931; clustered bootstrap 0.874–1.0; κ=1.0, independence verified);
  marker precision **0.814** (35/43; Wilson 0.674–0.903), recall vs independent
  sweep **0.972**; grounding judgment κ=0.494 (Moderate — honest disagreement);
  draft conformance 1.00. CI gate armed at each baseline − 0.05; unverified
  draft quotes fail the gate outright. 5-cluster census caveat printed with the CIs.
- **UI**: four new lazily-loaded sections (authority click-to-highlight into part
  and U.S.C. texts; equal-weight two-family grounding table with marker → document
  highlight; draft viewer with visible placeholders; OGC-01 eval with CIs and
  provisional labels). Playwright audit: **two consecutive fully clean local
  passes** + clean deployed-URL pass; axe zero violations (all impacts, local),
  zero serious/critical (deployed); 1440/768/375 no overflow; disclaimers
  (§333 + not-legal-advice) above the fold.
- **Zero-cost**: allow-list extended exactly per EXTEND-OGC01 §2 (uscode.house.gov,
  archives.gov, reginfo.gov — path-pinned); no new secrets; CourtListener/QuantGov/
  api.data.gov never used. The Cloudflare API token was **rolled** at the start of
  this pass (old value invalidated; secret re-set 2026-07-29T01:18Z).

## Independent reviews (author≠blesser) — all findings fixed

- **Validator (Opus): FAIL → fixed.** Negation-bypass in the classifier
  (negation-free gaps, deadline-idiom exception, passive-family guard + regression
  tests), fail-open eval gate (None metrics now fail closed), stale published
  drafts (export dir rebuilt each run), "and"-joined citation lists + nested
  subsections parse, part-scoped draft verification corpus, census dedupe,
  production asserts → raises.
- **Eval auditor: FAIL → fixed.** Degenerate link kappa now reported as raw
  agreement + None (never a fabricated 1.0); bootstrap relabeled
  "cluster-resampling range — not a calibrated 95% interval"; ICC/design-effect/
  effective-n added; deterministic cluster keys; missing baseline floors fail
  closed; recall denominators respect judged genuineness with pending counts;
  grounding kappa banded (0.49 Moderate) with an explicit below-0.61 trust note;
  gate now covered by tests; bootstrap percentile off-by-one fixed.
- **Security reviewer: PASS**; hardening applied anyway (redirect-hop allow-list
  re-checks, digest-pinned zip cache with size ceiling, single-quote + URL
  coverage in the draft quote/fabrication gates, case-tolerant delimiter
  neutralization, exact-URI namespace exemption in the zero-cost checker).
- **Neutrality reviewer: PASS** (zero blocking violations; verdict verbatim:
  "NEUTRALITY: PASS"). Both advisories applied: gate accept/reject badges moved
  to neutral tokens; draft analysis sections renumbered III–VIII.
- Shipped point estimates were unchanged by all fixes; the site was rebuilt,
  re-audited (two consecutive fully clean Playwright passes + clean deployed
  pass), and redeployed.

## De-scoped (sanctioned) — unchanged

OFAC 50% ownership graph, OSCAL, SLSA/cosign/Scorecard, Groq escalation, Inspect
wrapper, commit signing (BUILD.md order); CourtListener, QuantGov, outcome
prediction, ranked repeal lists, Ch. V/X expansion (EXTEND-OGC01 §6 — forbidden,
not merely de-scoped).

## Adjudication worklist status

**0/251 core + 0/306 OGC-01 adjudicated** — docs/ADJUDICATE.md holds both
numbered worklists; after each session `just eval && just build-web`, commit,
push; metrics and labels restate automatically from the JSONL.

## Next actions for the owner

1. Adjudicate gold labels (both worklists) — the single highest-value follow-up.
2. Note: the rolled Cloudflare token value transited this session's local
   transcript (you asked me to roll it via the browser). Roll it again at your
   convenience for full hygiene: dash.cloudflare.com → API Tokens → Roll, then
   `gh secret set CLOUDFLARE_API_TOKEN`.
3. Optional hardening: branch protection + PR-only main; signed commits;
   narrowing `.claude/settings.json` Bash allowances.
4. Optional next phases: OFAC ownership module, OSCAL, SLSA, Fiscal Data demo.

---

## Blueprint-alignment pass (2026-07-29)

Executed against `Treasury GenAI Architecture Blueprint.md` (committed at repo
root). Owner decisions: committed invariants override the blueprint on every
conflict; all four implementable feature deltas built; temporal-versioning
compare skipped and documented. The full reconciliation is
`docs/BLUEPRINT-ALIGNMENT.md` (realized / neutral equivalent / excluded with
the controlling invariant named).

**Shipped:**
- Client-side lexical search (precomputed inverted index, `reglens/search_index.py`;
  BM25 in the browser with a documented tokenizer twin; 4 MiB fail-closed cap;
  1.26 MB actual) over 950 claims, 112 U.S.C. sections, 185 CFR sections, 6 drafts.
- Title 31 hierarchy browser (`reglens/structure.py` — offset-validated section
  spans over the exact published part texts; per-part counts pinned in tests;
  rejected-candidate transparency counter — the corpus's single rejected
  candidate is part 223's in-text "§ 223.16 Department Circular No. 570 list…"
  cross-reference line, correctly refused as a heading).
- Authority cross-reference view (part ↔ U.S.C., both directions, shared
  authorities surfaced; retrieval-only copy).
- Three OFR amendatory verb forms (add / revise / remove-and-reserve,
  placeholder designations, rendered self-description "no amendment is
  proposed"), APA procedural-elements checklist (structural presence only),
  and a per-draft provenance dossier (model, decoding params, prompt/system
  SHA-256, part-snapshot digest labeled "context of record; not sent to the
  model").

**Audit loop:** validator (Opus) PASS-WITH-FIXES — its HIGH (set-out gate
fail-open on multi-paragraph/extra-blank-line set-out) fixed: the gate now
verifies every paragraph up to the next numbered instruction and treats an
empty region as a defect, regression-tested; security reviewer PASS — its
medium (client `..` traversal defense-in-depth) fixed with a thrown-error
segment guard; neutrality reviewer **PASS**, both advisories applied (dead
success/danger CSS tokens deleted; drafts self-describe). Drafts regenerated
6/6 under the stricter gate; all metrics unchanged (core F1 0.520, fidelity
1.000; OGC-01 link F1 1.0, class acc 0.884, marker P 0.814 / R 0.972, drafts
1.00; provisional labels unchanged, 0/251 + 0/306 adjudicated).

**Verification:** 150 pytest + 14 node tests green; ruff/pyright strict/
zero-cost green; two consecutive fully clean identical Playwright audits
locally (fold checks at 1440/768/375, all four search result types expand,
tree → section highlight, cross-refs, APA group, dossier, axe zero
violations) plus a fully clean identical pass against
https://reglens-31.pages.dev; all four CI workflows green at eedb6ea.

**Excluded by invariant (see BLUEPRINT-ALIGNMENT.md):** vulnerability
matrices / deference risk scores / deregulatory target reports (§5),
Regulations.gov comment ingestion (api.data.gov key ban), FinCEN/IRS bureau
templating (scope + §333), Form 450/RBAC lockout (no-auth non-goal +
restricted PII), pgvector/Memgraph/LangChain/live chat (zero-infra static
export), Llama-3-70B fine-tune (non-goal + hardware).

## Front-end revamp — OGC-01 mockup framing (2026-07-29, second pass)

Comprehensive front-end revamp making the site legible as an independent
mockup of Treasury AI use case OGC-01. Shipped:

- **About this demonstration** (`AboutSection.tsx` + `reglens/use_case_inventory.py`
  + `reglens/ingest/inventory.py`): Treasury's OGC-01 inventory row quoted
  verbatim from a pinned content-addressed snapshot of the official CSV
  (`home.treasury.gov`, exact-path allow-list entry; provenance shown: URL,
  fetch date, SHA-256), why-chosen numbers computed from the snapshot (129
  use cases, sole General Counsel entry, 1 of 4 high-impact), the "Looper
  Bright" [sic] note, and a traceability map linking each inventory-stated
  output to its on-page neutral-equivalent module. Hero gained the mockup
  line; footer gained the inventory attribution.
- **IA regroup**: About + four anchored CollapsibleSection groups
  (Extraction open by default; Explore, OGC-01 modules, Evaluation
  collapsed) behind one unified reveal pattern; sticky 5-link PageNav with
  open-scroll-focus hash navigation working from any collapsed state;
  RejectedClaims moved adjacent to the extraction panes; heading hierarchy
  h1 → h2 groups → h3 sections.
- **Shared primitives** (`web/app/components/ui/`): HighlightedText,
  CollapsibleSection, ExpandableGroup, useLazyJson, MetricCard +
  metric-format — the 5×-duplicated highlight logic and 6×-duplicated
  lazy-fetch blocks deleted (net −366 lines in the migration commit).
- **CI guards**: disclaimer-and-framing grep in ci.yml + deploy-pages.yml
  (invariant 4 was documented but unenforced); web tests now run in CI;
  export-replay guard re-derives `web/public/data` from committed snapshots
  and fails on drift; the deploy job no longer runs any package install
  with the Cloudflare token in scope (artifact handoff from verify).

Audit loop: neutrality-reviewer PASS-WITH-ADVISORIES (4 applied: quoted
table values, truncation ellipsis, unresolved category listed, "ranked"
not "scored"); security-reviewer PASS-WITH-FIXES (deploy-job isolation,
digest-pinned contract test + replay guard, exact-path allow-list tier +
port/dot-segment refusal, snapshot tests assert instead of skip, manifest
pin check — all applied); validator (Opus) PASS-WITH-FIXES (in-flight
promise sharing in useLazyJson so a second search submit is never dropped,
1.5 s degrade-open for hash navigation, honest rename of the source-marker
test, ExpandableGroup dead default toggle deleted — all applied). Known
accepted LOW: Authority and CrossRef each fetch `authority.json` into
their own hook instance (second hit is browser-cached).

Verification: 167 pytest + 25 node tests green; ruff/pyright strict/
zero-cost green; export replay byte-identical; full Playwright button-walk
(nav walk, deep links, every expander class, all four search result types,
keyboard, axe with all groups open, three viewports) — two consecutive
identical fully clean local passes and one identical clean pass against
https://reglens-31.pages.dev; all four workflows green at 6236e7b. OGC-01
feature-gap research: the inventory's three stated outputs are the ONLY
publicly documented capabilities, and all three already have shipped
neutral equivalents — no backend features were missing; the gap was
presentational and is now closed. Metrics and provisional labels
unchanged (0/251 core + 0/306 OGC-01 adjudicated; worklists still open).

## Multi-page revamp — sidebar app shell, GSAP motion, impeccable gate (2026-07-29, third pass)

The single long page became a 12-route working tool (user-directed; head
adcea60, live at https://reglens-31.pages.dev). Shipped: persistent USWDS
sidebar (grouped EXTRACTION / EXPLORE / OGC-01 MODULES / EVALUATION, exact
aria-current, mobile drawer with focus trap + Escape + role=dialog +
inert background), layout-level skip link/disclaimer/footer (§333 on every
page), trailingSlash directory export, task-first Overview (hero + count-up
stats + condensed OGC-01 framing + ten task cards + pipeline strip), full
About on /about with per-module traceability links, legacy #hash → route
forwarding (mount + hashchange), per-route h1 focus on client navigation.
Motion (gsap + @gsap/react, GreenSock Standard License — free, no card,
STACK.md row): 220 ms entrance, overview stagger, count-up, highlight pulse
— all inside prefers-reduced-motion guards with DOM authored in final
state; opacity-not-autoAlpha so focus targets stay focusable. impeccable
v3.4.0 (Apache-2.0, exact pin): PRODUCT.md/DESIGN.md briefs, detector CI
step over authored source (two justified USWDS exceptions recorded in
.impeccable config; puppeteer postinstall blocked durably by web/.npmrc
ignore-scripts; update phone-home disabled via updateCheck:false).

Audit loop (author≠blesser): neutrality PASS-WITH-ADVISORIES (titles
neutralized to "Grounding markers (two-sided)" and "Evaluation — core
metrics (provisional)", card-copy dedup, footer attribution now links to
/about — all applied); security PASS-WITH-FIXES (ignore-scripts, deploy
verify job gets the all-pages disclaimer loop, null-delimited CI loop,
zero-cost scan exclusion documented, GSAP license noted in DATA_LICENSE.md
— all applied); validator (Opus) PASS-WITH-FIXES (build-before-test in
both workflows — routes-contract reads web/out; pulse resolves
var(--soft-blue) before tweening; Overview h1 joins the focus contract;
drawer closes on same-page clicks; dead footer branch removed — all
applied).

Verification: 167 pytest + 35 node tests green; ruff/pyright strict/
zero-cost/detector green; per-route contract pins §333 + sole-h1 +
aria-current on all 12 emitted pages; rewritten multi-page Playwright
walk (~50 checks: nav walk with focus assertions, every tool control,
four search result types, legacy hashes, skip link, drawer keyboard,
reduced motion, axe zero violations on all 12 routes, three viewports) —
two consecutive identical fully clean local passes and one identical
clean pass against the deployed URL; all four workflows green at adcea60.
Metrics and provisional labels byte-identical (0/251 core + 0/306 OGC-01
adjudicated; worklists still open).
