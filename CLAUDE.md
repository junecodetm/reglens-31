# CLAUDE.md — RegLens-31 (Auditable, Laptop-Local Regulatory Intelligence for Treasury)

> Decomposed 2026-07-28 per §0 (the `/bootstrap` pass). This file is the short always-on core; component docs are `@`-imported at the bottom. The original 55 KB master spec is preserved in git history (initial commit).

## 0. Component file map

Decomposition is DONE. This table is the index of where each part of the spec lives.

| Spec section | Lives in | Status |
|---|---|---|
| 0 Decomposition map | `CLAUDE.md` (this file) | done |
| 1 Purpose & non-goals | `CLAUDE.md` (below) | done |
| 2 Invariants | `CLAUDE.md` (below; enforcement in hooks/CI) | done |
| 3 Zero-cost stack + free/no-card table | `docs/STACK.md` | done |
| 4 Repo structure | `docs/ARCHITECTURE.md` | done |
| 5 Coding standards | `CLAUDE.md` (short, below) + `docs/STANDARDS.md` | done |
| 6 Command surface | `docs/COMMANDS.md` + `justfile` | done (unbuilt recipes are stubs that exit 1) |
| 7 Git workflow | `docs/CONTRIBUTING.md` | done |
| 8 Architecture & data flow | `docs/ARCHITECTURE.md` | done |
| 9 Data sources + exclusion list | `docs/DATA_SOURCES.md` | done |
| 10 Entity resolution | `docs/ENTITY_RESOLUTION.md` | done |
| 11 Evaluation methodology | `docs/EVALUATION.md` | done |
| 12 Security & threat model | `docs/SECURITY.md` | done (`.github/workflows/` YAML = Phase 0/5 work) |
| 13 Governance mapping | `docs/GOVERNANCE.md` | done (`governance/` artifacts = Phase 4 work) |
| 14–15 Build plan + W1 tests + [VERIFY] appendix | `docs/BUILD_PLAN.md` | done |
| 16 README | `README.md` | skeleton + verbatim disclaimer; prose fills in per phase |
| 17 Skills | `.claude/skills/<name>/SKILL.md` (5 skills) | done |
| 18 Subagents | `.claude/agents/<name>.md` (3 agents) | done |
| 19 Hooks | `.claude/settings.json` + `.claude/hooks/` | done (hooks read stdin JSON; `$CLAUDE_FILE_PATH` is defunct) |
| 20 Permissions | `.claude/settings.json` | done |
| 21 "Do not do this" | `CLAUDE.md` (below) | done |
| 22 Pre-submission checklist | `docs/CHECKLIST.md` | done |
| — | `EXTEND-OGC01.md` (repo root) — OGC-01 extension spec: authority/grounding/draft stages, §5 neutrality rules, eval extension | done |
| — | `BUILD.md` (repo root) — single-pass build execution prompt; kept as a process-transparency artifact | done |
| — | `scripts/check_zero_cost.py` | done (real allow-list check: pinned actions, dependency + host allow-lists) |
| — | `reglens/corpus.py` — canonical corpus scope + the executable FR inclusion rule | done |

### Documents added after decomposition (2026-07-30 audit — these existed but were missing from this map)

| File | What it covers |
|---|---|
| `docs/PROGRESS.md` | Running build log: what was done per pass, and the sanctioned de-scope list |
| `docs/ADJUDICATE.md` | Generated adjudication worklist for the gold set (machine-proposed labels awaiting human review) |
| `docs/ANNOTATION_GUIDELINES.md` | What counts as an obligation; minimal-span and tie-breaking rules (docs/EVALUATION.md protocol) |
| `docs/OGC01-ALIGNMENT.md` | How the three EXTEND-OGC01 stages map to the OGC-01 inventory row |
| `docs/BLUEPRINT-ALIGNMENT.md` | Realization map against the Treasury GenAI Architecture Blueprint, incl. invariant-cited exclusions |
| `docs/M25-21-CROSSWALK.md` | OMB M-25-21 minimum-practices crosswalk to concrete `governance/` artifacts |
| `docs/Treasury GenAI Architecture Blueprint.md` | Reference source document for `BLUEPRINT-ALIGNMENT.md` |
| `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `DATA_LICENSE.md` (repo root) | Contributor path, conduct policy, data provenance + licence terms |

## 1. Project purpose & non-goals

**What this is.** RegLens-31 is a solo-built, zero-cost, auditable prototype that ingests U.S. federal regulatory and sanctions data and extracts structured, individually source-verified regulatory obligations — with a real evaluation harness and governance-as-code. It is a job-application artifact for U.S. Treasury "IT Specialist (Artificial Intelligence)," announcement 26-DO-12891471-DH, GS-2210, closing 09/21/2026. It targets the announcement's language on "secure & ethical deployment of AI," "cybersecurity-by-design and DevSecOps," "compliance with federal mandates and Executive Orders," and the selective factor "implement AI solutions in production or test environments." It delivers exactly the two required artifacts: a source-code repository (README + approach/tools/assumptions docs) and a deployed, browser-testable prototype URL.

**RE-AUDIT DECISION: MODIFY (keep the core concept, re-weight it and correct the stack).** Four corrected decisions:

1. **Capability 1 (Obligation Extraction + fail-closed provenance gate) is the finished, polished HEADLINE.** It is instantly legible — click any extracted obligation and the exact verbatim source span highlights; a banner shows "N claims rejected by the provenance gate." It is fully finishable, and it maps directly to Treasury's own named priority use-case family "Document Processing and Regulatory Intake" and to the only Departmental Offices high-impact use case, OGC-01 "Regulatory Reform Tool." *Why this beats the OFAC finding as the opener:* the value ("every claim is provably grounded in the primary source, and lies are auto-rejected") is legible in one glance to a non-expert reviewer, whereas the 50% Rule insight requires domain setup.
2. **Local-first inference on the Apple M4 becomes a HEADLINE feature, not a fallback.** "Runs entirely on a laptop with no third-party AI data egress" is a stronger federal story (data sovereignty, ATO/FedRAMP friction avoided, air-gap viability) and directly aligns with M-25-21's encouragement of models that require less data and compute. *Reason for change:* the new hard zero-cost constraint makes cloud inference marginal anyway, so we convert a constraint into a differentiator.
3. **Capability 2 (OFAC 50% Rule ownership graph) is DEMOTED to a clearly-labeled secondary/analytical module, pre-seeded so it always demos.** It stays because it is a genuine "wow," but it is not the first thing the reviewer sees, because its live-coverage risk is real (see `docs/ENTITY_RESOLUTION.md`). It ships pre-seeded with the documented Oleg Deripaska → EN+ Group / RUSAL / Basic Element / B-Finance case so the demo never depends on live-match luck.
4. **Capability 3 (Evaluation + Governance-as-code) stays as a co-headline** because it is precisely what a "secure & ethical deployment of AI" role is scored on, and it is cheap to finish to high quality.

**Why not pivot entirely?** The alternatives were scored on a consistent rubric (mission relevance, job-bullet coverage, technical impressiveness, instant legibility, zero-cost feasibility, solo feasibility, failure risk). A pure eval/assurance harness scores high on impressiveness/feasibility but low on instant legibility; a Treasury Fiscal Data NL-query layer scores high on legibility/zero-cost but weaker on the "secure/ethical AI deployment" mission bullets; a prompt-injection demonstrator is impressive but narrow. The incumbent, once trimmed to "provenance-gated extraction as the headline + governance/eval co-headline + seeded ownership graph as a labeled extra," wins on the combined rubric because it covers the most job bullets while staying finishable. **Verdict: KEEP the concept, MODIFY the emphasis and stack. Do not pivot for novelty's sake.**

**Non-goals (write these down so scope never creeps):**
- Not a sanctions-screening product. It illustrates the 50% Rule; it does not screen transactions or make compliance determinations.
- Not a legal-advice tool. Every output is assistive, human-in-the-loop, "verify against the primary source."
- Not a live-updating hosted service the reviewer depends on. The reviewer URL is a pre-computed static export.
- Not multi-tenant, not authenticated, no user data, no fine-tuning.

## 2. Hard non-negotiable invariants

Each invariant names its enforcement mechanism. Invariants are enforced by hooks (local), CI (remote), and code (runtime) — not by good intentions.

1. **ZERO-COST INVARIANT (binding).** No component may require a credit card on file or create any possibility of a charge. No paid tier, no "add a card for higher limits," no trial that converts. *Enforcement:* (a) `docs/STACK.md` free/no-card table is the allow-list; (b) CI check `scripts/check_zero_cost.py` fails the build if a dependency, action, or service outside the allow-list appears; (c) a PreToolUse hook blocks `wrangler`/`gcloud`/`aws`/`flyctl`/`render` deploy commands that imply billed services. **The card-gated Groq Developer tier — "up to 10x higher limits" plus a 25% token discount — is PROHIBITED.**

2. **PROVENANCE-GATE INVARIANT (fail-closed).** Every extracted claim MUST carry a verbatim quoted span. A deterministic substring check discards any claim whose quote is not an exact substring (after documented Unicode/whitespace normalization) of the fetched source text. Fail-closed: if verification cannot run, the claim is dropped, not kept. This is framed as an auditable correctness floor, not a novelty — citation grounding is now a commodity API feature (e.g., Anthropic's Citations API, GA on the Anthropic API and Google Cloud Vertex AI since 2025-01-23 returning `start_char_index`/`end_char_index`, and on Amazon Bedrock since 2025-06-30) — but running the check deterministically and fail-closed, locally, is the differentiator. *Enforcement:* `reglens/provenance.py::verify_span()` runs on every claim before persistence; a unit test asserts a fabricated quote is rejected; the UI renders rejected-claim counts.

3. **NO-RESTRICTED-DATA INVARIANT.** Never ingest, store, reference, or synthesize: BSA/SAR data; FinCEN Beneficial Ownership Information; taxpayer data; PII about private individuals; anything behind auth or paywalls; any Vixio (employer) data or work product. *Enforcement:* the data-source allow-list in `docs/DATA_SOURCES.md` is the only permitted fetch set; `reglens/ingest/allowlist.py` refuses any URL not on it; gitleaks + a custom Semgrep rule scan for restricted-data markers; PII redaction runs on all logs (`docs/SECURITY.md`).

4. **NON-AFFILIATION INVARIANT (31 U.S.C. §333).** The project must not use Treasury names, seals, or symbols in a way implying affiliation, and must not use a government-implying domain. A visible non-affiliation disclaimer appears in the README, the site footer, and the repo description. *Enforcement:* a CI grep asserts the disclaimer string is present in `README.md` and the built site; the deploy domain is a neutral `*.pages.dev` or a personal domain.

5. **DETERMINISTIC-REPLAY INVARIANT.** Every pipeline run is reproducible from committed raw snapshots + pinned model + fixed seed/temperature=0. *Enforcement:* raw source snapshots are content-addressed (SHA-256) under `data/raw/<sha>/`; eval CI runs against cached fixtures at $0 API cost; a "replay" test asserts identical outputs from identical inputs.

6. **HUMAN-IN-THE-LOOP INVARIANT.** No output is presented as authoritative. Every claim links to its primary source; the UI states the tool is assistive. *Enforcement:* the UI template includes the disclaimer band; the model card states intended use and limitations.

## 5. Coding standards (short — full text: `docs/STANDARDS.md`)

- Python 3.13, full type hints; `pyright` strict on `reglens/`; `ruff` lint + format — no unformatted code merges.
- Pydantic v2 models for every external payload and extracted record; no untyped dicts crossing module boundaries.
- Pure functions where possible; side effects (network, disk) isolated in `ingest/` and `store/`.
- Determinism: LLM calls at temperature 0 with a pinned model tag; every run records model id, prompt hash, input SHA.
- No secret in code; config via env + gitignored `.env` through `pydantic-settings`.
- Docstrings state inputs, outputs, and failure mode; every fail-closed path is commented as such.
- Tests: `pytest` + `respx`/`vcrpy` cassettes for HTTP + `hypothesis` for the provenance normalizer.

## 21. "Do not do this" failure-mode list

- Do NOT add a credit card to any service, ever. Do NOT enable Groq's Developer tier.
- Do NOT deploy a live backend the reviewer depends on. Ship a pre-computed static export.
- Do NOT ingest BSA/SAR, FinCEN BOI, taxpayer data, private PII, paywalled/authed content, or any Vixio data.
- Do NOT keep any extracted claim without an exact verbatim source span (fail-closed).
- Do NOT use Treasury names/seals/symbols to imply affiliation, or a government-implying domain.
- Do NOT present the OFAC ownership graph as a screening determination; it illustrates the 50% Rule with caveats.
- Do NOT equate GLEIF accounting-consolidation with 50%-Rule ownership.
- Do NOT let source text drive tool calls (prompt-injection).
- Do NOT let the demo depend on a network call or an API key.
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
@docs/BUILD_PLAN.md
@docs/CHECKLIST.md
