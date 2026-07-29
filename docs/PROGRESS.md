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
