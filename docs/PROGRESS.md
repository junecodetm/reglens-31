# PROGRESS — RegLens-31 single-pass build

> **Status: COMPLETE — no remaining work.** Built 2026-07-28 in one pass per BUILD.md.
> Live: **https://reglens-31.pages.dev** · Repo: **https://github.com/junecodetm/reglens-31**

## What was built (all verified)

- **Pipeline:** allow-list-enforced ingest (20 Treasury FR final rules + eCFR Title 31 parts 50/223/285/356/501; SHA-256 content-addressed snapshots + manifests) → local extraction (Ollama qwen3:8b, temp 0, fixed seed, JSON-schema-constrained, pinned tag + prompt/input SHA per run, 80K-char disclosed per-document cap) → **fail-closed provenance gate** (character-wise NFKC + whitespace normalizer with offset map; exact substring; every failure path rejects) → SQLite + DuckDB/Parquet stores → static export.
- **Results:** 25 documents, **950 claims accepted, 163 rejected** by the gate, 7 chunks dropped fail-closed on invalid model output. Fabricated-quote rejection proven by unit + hypothesis tests AND visible in the UI counter + rejected-claims transparency section.
- **Eval (honest, provisional):** 251-provision gold set, two disclosed strata, two frozen proposal passes by different models (fable-5 / sonnet-5). **P=0.434 (95% Wilson 0.329–0.546; clustered bootstrap 0.208–0.556), R=0.647 (Wilson 0.510–0.764; bootstrap 0.378–0.967), F1=0.520 (bootstrap 0.278–0.658)** — TP=33 FP=43 FN=18; citation fidelity 1.000 (guardrail), **cross-model κ=0.938 (Almost perfect)**, effective n≈122 (design effect 2.06), per-stratum breakdown in eval.json. Every metric carries: *"Provisional — machine-proposed labels, human-adjudicated: 0/251."* CI regression gate armed at F1 baseline 0.520 − 0.05.
- **UI:** obligation list → click → exact span highlighted + scrolled in the primary source; §333 disclaimer above the fold at 1440/768/375; model-generated fields labeled; axe **zero violations**; fully keyboard operable. Playwright audit: **two consecutive fully clean passes** locally + clean pass on the deployed URL.
- **Security/governance:** SHA-pinned least-privilege workflows (CI, security, eval-gate, verify-then-deploy); CodeQL, pip-audit, checksum-verified gitleaks/osv-scanner/syft, semgrep; SBOM artifact; CSP + security headers; real zero-cost allow-list checker; model/data cards, AI impact assessment, monitoring + rollback plans; DATA_LICENSE.md; CONTRIBUTING + CoC. Independent subagent reviews (security, statistics, code quality) ran and **every finding was fixed** (statistics re-verified by the auditor).

## De-scoped (BUILD.md's sanctioned order) and why

1. **OFAC 50% ownership graph** — first in the de-scope order; design + seeded Deripaska case fully documented in docs/ENTITY_RESOLUTION.md for a future phase.
2. **OSCAL component-definition** — substantive governance artifacts are present; OSCAL validation deferred.
3. **SLSA L3 provenance**; 4. **Groq escalation** (local-only is the stronger air-gap story); 5. **Inspect AI wrapper** (the deterministic in-repo harness owns all statistics per docs/EVALUATION.md); 6. **Commit signing** (no key on this machine; not in the DoD).

## Adjudication worklist status

**0/251 adjudicated** — docs/ADJUDICATE.md is a numbered worklist (~13 evenings at ~20/evening). After each session: `just eval && just build-web`, commit, push; metrics and their label restate automatically from the JSONL.

## Security notes / next actions for the owner

1. **Roll the Cloudflare API token** (Pages:Edit) — its value passed through this build session's transcript; GitHub push protection blocked the one accidental commit attempt and `.playwright-mcp/` is now gitignored. Roll at dash.cloudflare.com → API Tokens, then `gh secret set CLOUDFLARE_API_TOKEN`.
2. Adjudicate gold labels (see above) — the single highest-value follow-up.
3. Optional hardening: branch protection + PR-only main, signed commits, narrowing `.claude/settings.json` `Bash(git:*)/Bash(gh:*)` allowances, per-stratum precision weighting once adjudication yields trusted labels.
4. Optional next phases: OFAC ownership module, OSCAL, SLSA, Fiscal Data demo.
