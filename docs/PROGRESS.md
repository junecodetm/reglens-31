# PROGRESS — RegLens-31 single-pass build

> Status: IN PROGRESS — full-corpus extraction is running; final eval + audit passes land when it completes. This file is updated at every checkpoint (BUILD.md §1).

## Built and verified

- **Scaffold + CI (green from first push):** uv/ruff/pyright-strict/pytest, SHA-pinned least-privilege workflows (`ci`, `security`, `eval`, `deploy-pages`).
- **Ingest:** allow-list-enforced (runtime refusal of any non-DATA_SOURCES.md URL), content-addressed snapshots with manifests; 25 documents (20 recent Treasury FR final rules + eCFR Title 31 parts 50/223/285/356/501, pinned point-in-time date).
- **Extraction:** Ollama qwen3:8b, temperature 0, fixed seed, JSON-schema-constrained, pinned tag + prompt/input SHA recorded per run; paragraph chunking; per-document checkpointing; fail-closed chunk error handling; disclosed per-document extraction cap (`total_chars`/`extracted_chars`).
- **Provenance gate (the heart):** character-wise NFKC + whitespace-collapse normalizer with an offset map; exact-substring check; accepted claims carry original-text highlight offsets; every failure path rejects (empty quote, no match, internal error). Hypothesis property tests + explicit fabricated-quote rejection test.
- **Gold set + eval:** 251 provisions, two disclosed strata, two independent model annotation passes (`proposed_by` recorded), `adjudicated: false` on every record, `docs/ADJUDICATE.md` worklist (~20/evening), metrics (P/R/F1, Wilson, clustered bootstrap, ICC/design effect, kappa, citation-fidelity guardrail), CI regression gate at $0 on committed fixtures. All published metrics carry the exact Provisional label; the adjudicated count is derived from the JSONL.
- **UI (live):** https://reglens-31.pages.dev — obligation list → click → exact span highlighted in the primary source; rejection counter in the header (real, non-zero); rejected-claims transparency section; evaluation section with CIs and the honesty label; §333 disclaimer above the fold at 1440/768/375; axe: zero violations; fully keyboard operable.
- **Store:** SQLite system of record + DuckDB Parquet export with analytics summary.
- **Security/governance:** CodeQL (py+ts), pip-audit, osv-scanner (2 real findings fixed via npm overrides), gitleaks, semgrep, syft CycloneDX SBOM artifact; real zero-cost allow-list checker (actions/deps/hosts); model card, data card, AI impact assessment, monitoring plan, rollback plan; DATA_LICENSE.md; CONTRIBUTING + Code of Conduct.

## De-scoped (sanctioned order from BUILD.md §3) and why

1. **OFAC 50% ownership graph** — first item in the de-scope order; the extraction+eval headline is complete without it. Design, caveats, and the seeded Deripaska case remain fully documented in docs/ENTITY_RESOLUTION.md for a future phase.
2. **OSCAL component-definition** — second de-scope item; the substantive governance artifacts (cards, assessment, plans) ARE present.
3. **SLSA L3 provenance** — third de-scope item.
4. **Groq escalation path** — fourth; the build is local-only (stronger air-gap story, zero rate-limit risk).
5. **Inspect AI harness wrapper** — the deterministic in-repo harness (`reglens/eval/harness.py`) owns all statistics (Wilson/bootstrap/kappa were always planned in-repo per docs/EVALUATION.md `[VERIFY]`); an Inspect task wrapper adds a dependency without adding rigor at this scope.
6. **Commit signing** — no signing key configured on this machine; not in the Definition of Done. Enable later via `git config commit.gpgsign true` + a GitHub-registered key.

## Adjudication worklist status

251/251 items pending human adjudication (`docs/ADJUDICATE.md`, ~13 evenings at 20/evening). Metrics are labeled "Provisional — machine-proposed labels, human-adjudicated: 0/251" and restate automatically as items are adjudicated.

## Security notes for the owner

- The Cloudflare API token (Pages:Edit scope only) was created via a browser session driven inside this build session; its value passed through the session transcript. **Recommended: roll the token** (dash.cloudflare.com → API Tokens → roll) and update the repo secret via `gh secret set CLOUDFLARE_API_TOKEN`. GitHub push protection blocked an accidental commit of a Playwright page snapshot containing it; `.playwright-mcp/` is now gitignored and nothing under it is tracked.

## Next actions for the owner

1. Adjudicate gold labels (~20/evening; instructions at the top of docs/ADJUDICATE.md), then `just eval && just build-web`, commit, push — metrics and their label restate automatically.
2. Roll the Cloudflare token (above).
3. Optional next phases: OFAC ownership module (seeded Deripaska case), OSCAL component-definition, SLSA provenance, branch protection + signed commits.
