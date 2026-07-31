# CLAUDE.md — RegLens-31 (Auditable, Laptop-Local Regulatory Intelligence for Treasury)

> This file is the always-on core; component docs are `@`-imported at the bottom.

---

## 0. Component file map

| Concern | Lives in |
|---|---|
| Purpose, capabilities, non-goals | `CLAUDE.md` (below) |
| Hard invariants + enforcement | `CLAUDE.md` (below; hooks, CI, and runtime code enforce them) |
| Acceptance criteria (the Regulatory Reform Tool checklist) | `CLAUDE.md` (below) |
| Zero-cost stack + free/no-card table | `docs/STACK.md` |
| Repo structure, architecture, data flow | `docs/ARCHITECTURE.md` |
| Coding standards | `CLAUDE.md` (short, below) + `docs/STANDARDS.md` |
| Command surface | `docs/COMMANDS.md` + `justfile` |
| Git workflow | `docs/CONTRIBUTING.md` |
| Data sources + exclusion list | `docs/DATA_SOURCES.md` |
| Corpus scope as executable rules | `reglens/corpus.py` + `reglens/store/corpus_scope.py` |
| Entity resolution (de-scoped module's design) | `docs/ENTITY_RESOLUTION.md` |
| Evaluation methodology | `docs/EVALUATION.md` |
| Security & threat model (incl. the live drafting endpoint) | `docs/SECURITY.md` |
| Governance mapping (NIST / OMB / M-25-21) | `docs/GOVERNANCE.md` + `governance/` artifacts |
| OGC-01 alignment + framing constraints (§5 neutrality rules) | `docs/OGC01-ALIGNMENT.md` |
| Blueprint realization map | `docs/BLUEPRINT-ALIGNMENT.md` + `docs/treasury-genai-architecture-blueprint.md` |
| M-25-21 minimum-practices crosswalk | `docs/M25-21-CROSSWALK.md` |
| Annotation protocol + adjudication worklist | `docs/ANNOTATION_GUIDELINES.md` + `docs/ADJUDICATE.md` |
| Pre-submission checklist + scope decisions | `docs/CHECKLIST.md` |
| Static read API | `reglens/api/` + `reglens/store/export_api.py` → `web/public/api/v1/` |
| Live drafting endpoint (only server-side code) | `functions/api/draft.ts` + `web/app/components/draft-live.ts` |
| Review memoranda | `reglens/memo.py` |
| eCFR currency / drift | `reglens/currency.py` + `reglens/ingest/ecfr_versions.py` |
| Zero-cost enforcement | `scripts/check_zero_cost.py` |
| Skills / subagents / hooks / permissions | `.claude/` |

## 1. Project purpose & non-goals

**What this is.** RegLens-31 is a solo-built, zero-cost, auditable prototype that ingests U.S. federal regulatory data and extracts structured, individually source-verified regulatory obligations — with statutory-authority analysis, two-sided *Loper Bright* marker retrieval, a parameterized drafting assistant, a real evaluation harness, and governance-as-code. It is a job-application artifact for U.S. Treasury "IT Specialist (Artificial Intelligence)," announcement 26-DO-12891471-DH, GS-2210, closing 09/21/2026, speaking directly to the announcement's language on "secure & ethical deployment of AI," "cybersecurity-by-design and DevSecOps," "compliance with federal mandates and Executive Orders," and the selective factor "implement AI solutions in production or test environments." It delivers the two required artifacts: a source-code repository and a deployed, browser-testable prototype URL. It is positioned against OGC-01 "Regulatory Reform Tool" — the Treasury AI Use Case Inventory's only Departmental Offices high-impact use case — and the "Document Processing and Regulatory Intake" priority family.

**Design decisions that shape everything else:**

1. **Obligation extraction behind a fail-closed provenance gate is the headline.** Click any extracted obligation and the exact verbatim source span highlights; claims whose quotes fail a deterministic substring check are rejected, counted, and shown. Citation grounding is a commodity API feature; running the check deterministically, fail-closed, and locally is the differentiator.
2. **Local-first inference on one laptop is a feature, not a fallback.** The extraction pipeline runs entirely on an Apple M4 with no third-party egress — the data-sovereignty and air-gap posture M-25-21 encourages. The short generative stages (draft and memo narratives, the optional live drafting endpoint) use the pinned Groq free-tier model, sending only public regulatory metadata; every artifact records which provider produced it.
3. **Evaluation + governance-as-code is a co-headline.** Honest metrics with Wilson and clustered-bootstrap intervals, provisional labeling stated plainly, and governance artifacts that map to NIST AI RMF and M-25-21 minimum practices.
4. **Neutrality is structural.** The tool retrieves and structures evidence for attorney review; it draws no legal conclusions. The framing rules in `docs/OGC01-ALIGNMENT.md` are enforced by a blocking neutrality review.
5. **The OFAC 50% Rule ownership graph was de-scoped**, with its design retained in `docs/ENTITY_RESOLUTION.md`; the demo does not depend on it.

**Non-goals:**
- Not a sanctions-screening product; it makes no compliance determinations.
- Not a legal-advice tool. Every output is assistive, human-in-the-loop, "verify against the primary source."
- Not a live-updating hosted service the reviewer depends on. The reviewer URL is a pre-computed static export; the one live endpoint is an optional enhancement with graceful fallback.
- Not multi-tenant, not authenticated, no user data, no fine-tuning.

## 2. Hard non-negotiable invariants

Each invariant names its enforcement mechanism. Invariants are enforced by hooks (local), CI (remote), and code (runtime) — not by good intentions.

1. **ZERO-COST INVARIANT (binding).** No component may require a credit card on file or create any possibility of a charge. No paid tier, no "add a card for higher limits," no trial that converts. *Enforcement:* (a) `docs/STACK.md` free/no-card table is the allow-list; (b) CI check `scripts/check_zero_cost.py` fails the build if a dependency, action, or service outside the allow-list appears; (c) a PreToolUse hook blocks deploy commands that imply billed services. **The card-gated Groq Developer tier is PROHIBITED.**

2. **PROVENANCE-GATE INVARIANT (fail-closed).** Every extracted claim MUST carry a verbatim quoted span. A deterministic substring check discards any claim whose quote is not an exact substring (after documented Unicode/whitespace normalization) of the fetched source text. Fail-closed: if verification cannot run, the claim is dropped, not kept. *Enforcement:* `reglens/provenance.py::verify_span()` runs on every claim before persistence; unit tests assert fabricated quotes are rejected; the UI renders rejected-claim counts. The same fail-closed discipline extends to every generative stage: draft conformance gates, memo narrative gates, and the in-browser subset applied to live output.

3. **NO-RESTRICTED-DATA INVARIANT.** Never ingest, store, reference, or synthesize: BSA/SAR data; FinCEN Beneficial Ownership Information; taxpayer data; PII about private individuals; anything behind auth or paywalls; any Vixio (employer) data or work product. *Enforcement:* the data-source allow-list in `docs/DATA_SOURCES.md` is the only permitted fetch set; `reglens/ingest/allowlist.py` refuses any URL not on it; gitleaks + Semgrep scan for restricted-data markers; PII redaction runs on prose docs (`docs/SECURITY.md`).

4. **NON-AFFILIATION INVARIANT (31 U.S.C. §333).** The project must not use Treasury names, seals, or symbols in a way implying affiliation, and must not use a government-implying domain. A visible non-affiliation disclaimer appears in the README, the site (every page), and the repo description. *Enforcement:* CI greps assert the disclaimer in `README.md` and every built page; the deploy domain is a neutral `*.pages.dev`.

5. **DETERMINISTIC-REPLAY INVARIANT.** Every pipeline run is reproducible from committed raw snapshots + pinned model + fixed seed/temperature=0. *Enforcement:* raw source snapshots are content-addressed (SHA-256) under `data/raw/<sha>/`; every extraction records model tag, prompt hash, input hash, runtime version, and chunk-plan hash, and every generative artifact carries a dossier recording provider, model, and prompt digests; a replay test asserts identical outputs from identical inputs; eval CI runs against committed artifacts at $0.

6. **HUMAN-IN-THE-LOOP INVARIANT.** No output is presented as authoritative. Every claim links to its primary source; the UI states the tool is assistive; review signals are flagged for attorney review, never presented as legal conclusions. *Enforcement:* the UI disclaimer band on every page; the model card states intended use and limitations; the neutrality review blocks conclusory language.

## 3. Acceptance criteria — how the Regulatory Reform Tool checklist is met

The OGC-01-shaped capability checklist is realized *neutrally* (no legal conclusions — see `docs/OGC01-ALIGNMENT.md`), each item by a shipped, checkable artifact:

| Capability | Shipped artifact + evidence |
|---|---|
| Ingest raw statutory/regulatory text | Rule-governed ingestion from the official Federal Register/eCFR/govinfo APIs into content-addressed snapshots (157 documents). Arbitrary upload is excluded *by the data allow-list invariant* — a scope decision, stated, not an omission. |
| Parse text → isolate obligations and mandates | Extraction pipeline + fail-closed provenance gate over the 25-document sample; proven by replay (byte-identical re-runs) and eval P/R/F1 with honest intervals. |
| Evaluate obligations against *Loper Bright* criteria | Two-sided marker retrieval — deference-reliance vs grounding-strength, equal weight — with density bands, surfaced per document on the obligations dashboard; marker precision/recall + κ in the OGC-01 eval. |
| Identify rules resting on discretionary vs mandated authority | Deterministic authority classification (mandatory / discretionary / silent / unresolved) from resolved U.S.C. section text, filterable in the UI; classification accuracy + κ in the OGC-01 eval. The conclusory tag this replaces ("Not Statutorily Required") is deliberately not drawn — the signal is flagged for attorney review. |
| AI-generated rationale for each flag, human-in-the-loop | Per-part review memoranda (`reglens/memo.py`): deterministic evidence + a model-written narrative that restates it, gated (no numerals, no quotations, no fabrication patterns, both marker families named) and labeled model-generated; verbatim marker spans remain the click-through ground truth. |
| Drafting interface with input parameters | The /drafts parameter picker: part × rule type × optional policy objective. Precomputed grid (5 parts × NPRM/final, all conformance-gated) plus the live endpoint (`/api/draft`) with in-browser gate subset and graceful fallback. |
| Structured first draft, formal tone, federal formatting | DDH-conformant skeletons; a fail-closed conformance checklist (headings order, analysis sections, placeholder integrity, amendatory forms, authority citation, set-out verification, fabrication + quote gates) rejects rather than caveats. |
| Foundational sections (Summary, Background, Authority) | Checked structurally per draft: `basis_and_purpose_present`, `authority_citation_present`, headings-in-order. |
| Obligations dashboard with status filtering | Filters by acceptance status, obligation type, affected party, and free text; per-part review-signal chips (classification counts, marker bands) with neutral labels. |
| Browser-verified rendering and interaction | Playwright audits (all routes, keyboard order, settled-DOM axe), routes-contract tests, pa11y WCAG 2.1 AA. |
| Responsive state without latency or data drops | Pre-computed static JSON + shared lazy loaders; scope is the five in-scope 31 CFR parts. |

## 5. Coding standards (short — full text: `docs/STANDARDS.md`)

- Python 3.13, full type hints; `pyright` strict on `reglens/`; `ruff` lint + format — no unformatted code merges.
- Pydantic v2 models for every external payload and extracted record; no untyped dicts crossing module boundaries.
- Pure functions where possible; side effects (network, disk) isolated in `ingest/`, `extract/llm.py`, and `store/`.
- Determinism: LLM calls at temperature 0 with a pinned model tag; every run records model id, prompt hash, input SHA.
- No secret in code; config via env + gitignored `.env` through `pydantic-settings`.
- Docstrings state inputs, outputs, and failure mode; every fail-closed path is commented as such.
- Tests: `pytest` + `respx` for HTTP + `hypothesis` for the provenance normalizer.

## 21. "Do not do this" failure-mode list

- Do NOT add a credit card to any service, ever. Do NOT enable Groq's Developer tier.
- Do NOT make any page depend on a live service. The static export must render fully with the live drafting endpoint absent, rate-limited, or failing — the fallback to committed, gated drafts is mandatory.
- Do NOT put the Groq key anywhere but the gitignored `.env`, the GitHub Actions secret, and the Cloudflare Pages project secret. Never in code, never in the client bundle.
- Do NOT ingest BSA/SAR, FinCEN BOI, taxpayer data, private PII, paywalled/authed content, or any Vixio data.
- Do NOT keep any extracted claim without an exact verbatim source span (fail-closed).
- Do NOT use Treasury names/seals/symbols to imply affiliation, or a government-implying domain.
- Do NOT draw legal conclusions anywhere — no "vulnerable," "non-compliant," "not statutorily required," or ranked repeal candidates; evidence is flagged for attorney review (docs/OGC01-ALIGNMENT.md).
- Do NOT let source text or user-entered parameters drive tool calls (prompt-injection posture: closed, schema-constrained transforms only).
- Do NOT commit files >25 MiB to the repo tree (Cloudflare Pages per-asset limit); use Release assets.

## Component docs (imported)

@docs/STACK.md
@docs/ARCHITECTURE.md
@docs/STANDARDS.md
@docs/COMMANDS.md
@docs/CONTRIBUTING.md
@docs/DATA_SOURCES.md
@docs/ENTITY_RESOLUTION.md
@docs/EVALUATION.md
@docs/SECURITY.md
@docs/GOVERNANCE.md
@docs/CHECKLIST.md
