# Audited Zero-Cost Tech Stack + Free/No-Card Verification Table

> Decomposed from CLAUDE.md §3 (2026-07-28). Enforcement: this file's free/no-card table is the allow-list for the ZERO-COST INVARIANT (CLAUDE.md §2, invariant 1).

Pinned versions are targets to confirm at `uv lock` time; anything unconfirmed is marked `[VERIFY]`.

**Language / tooling:** Python 3.13 with `uv` (env + lock), `ruff` (lint+format), `pyright` (types), `pydantic` v2 (schemas). *Justification:* fast, reproducible, typed, all free/OSS.

**Inference (CORRECTED to local-first, hybrid):**
- **Primary: local on the Apple M4 MacBook Pro via Ollama 0.19+ (which shipped an MLX backend on Apple Silicon on 2026-03-30, a large speedup on all Apple Silicon; M4 gets the unified-memory wins but not the M5-only Neural Accelerator boost), or MLX-LM, with LM Studio as a GUI option (dual llama.cpp/MLX backend).** JSON-schema adherence enforced with Ollama's structured-output `format` parameter (pass a JSON Schema), or llama.cpp GBNF grammars / `--json`, or Outlines / XGrammar / llguidance for token-level constraint. *Justification:* no card, no egress, aligns with M-25-21's "less data and compute."
- **Model choice by RAM tier (exact M4 Pro/Max variant and RAM are unknown — guidance across tiers):** 16 GB → a 4–9B instruct model (Qwen 3.x ~9B or a Phi-4-mini class) at Q4; 24 GB → Mistral Small 3.2 24B or a ~14B model; 32 GB → Gemma 4 ~27–31B or a 30B-A3B MoE at Q4 (community reports ~100 tok/s class on the MoE); 48 GB → same with generous context headroom. Qwen 3.x is the strongest native JSON/structured-output family per current community testing; NuExtract-3-class specialized extractors are a fallback if general models underperform on span fidelity. Confirm exact model + quant at build time (docs/BUILD_PLAN.md test W1-1). *Honest caveat:* full-document field accuracy is still hard for all local extraction models (a 2026 Datalab-style benchmark shows local models trailing hosted Gemini/Datalab on field accuracy and much lower on whole-document accuracy) — which is exactly why the provenance gate + eval harness exist.
- **Secondary (hard cases only): Groq free tier** — per Groq's official rate-limit documentation, the free tier is **30 requests/min, 6,000 tokens/min, 14,400 requests/day per model, applied at the organization level (multiple keys do not bypass it)**; no credit card; cached tokens are excluded from rate-limit accounting; the Batch API is reportedly NOT on the free tier. Use only as an escalation path for documents the local model flags as low-confidence. The card-gated Developer tier ("up to 10x higher limits" + 25% token discount) is **prohibited** by invariant #1. *Realistic workload check:* a ≥200-provision gold set plus a few thousand extraction calls fits comfortably inside 14,400 RPD if batched over days; the binding constraint is 6,000 TPM on larger models, so long documents must be chunked. Local-first sidesteps both limits entirely.
- **Adapter pattern:** a thin `LLMProvider` interface (`local` | `groq`) so the engine is swappable and the whole pipeline can run local-only for the air-gap story.

**Storage (CORRECTED — Postgres dropped):** SQLite (system of record for small structured tables) + DuckDB (analytics, joins over Parquet) + Parquet artifacts committed to the repo (or to a GitHub Release asset if >25 MiB). *Justification:* Postgres needs a card-backed host; SQLite/DuckDB are zero-infra, and DuckDB is *more* impressive for an analytics-shaped join workload. Migrations are plain versioned SQL in `migrations/` (Alembic dropped — overkill without a server DB, and its removal does not weaken the "data platform" signal because DuckDB+Parquet is the stronger analytics story).

**Orchestration (CORRECTED — Dagster dropped as default):** plain, typed Python modules invoked by `just` locally and by GitHub Actions cron remotely, with idempotent, content-addressed steps. *Justification:* Dagster is heavy for a solo part-time build; a clean functional pipeline is easier to finish and audit. (Dagster remains an optional local-only stretch if time allows.)

**API / UI:** FastAPI `/v1` for local dev only (never the reviewer's dependency); Next.js 15.x `output: 'export'` static site + `@trussworks/react-uswds` 11.1.0 (React USWDS 3 component library, Apache-2.0, latest 11.1.0). **React 19 compatibility of react-uswds 11.x is `[VERIFY AT BUILD TIME]`** — test in week one; fallback is React 18, or plain USWDS 3 HTML/CSS if incompatible.

**Evaluation:** Inspect AI (UK AI Security Institute, MIT, `inspect-ai`; `inspect-ai` was at 0.3.130 as of 2025-09-07, actively developed) as the harness; it ships bootstrap/stderr-based aggregation and model-graded/F1 scoring, from which confidence intervals are computed. `promptfoo` optional for prompt regression. *Justification:* government-credible, open, CI-friendly at $0. *Note:* confirm at build time whether the current release exposes native Wilson-interval metrics; if not, compute them in `reglens/eval/metrics.py` (docs/EVALUATION.md).

**Observability (CORRECTED — hosted dropped):** `structlog` structured JSON logs + OpenTelemetry file/console exporter (GenAI semantic conventions, pre-stable) + Inspect logs. *Justification:* Langfuse/Phoenix self-host is free but is another service to babysit; file-based telemetry is zero-cost and air-gap-friendly. (Self-hosted Langfuse/Phoenix noted as optional local extras.)

**DevSecOps (all free/OSS on PUBLIC repos):** SHA-pinned least-privilege GitHub Actions; Renovate (free GitHub app on public repos); `pip-audit`; `osv-scanner`; `gitleaks`; CodeQL code scanning (free on public repos; GHAS only needed for private); Semgrep (free CLI + community rules); CycloneDX SBOM via `syft`; distroless/Chainguard-Wolfi base images for any container; signed commits; `cosign` keyless (Sigstore, OIDC via GitHub — no card) signing + SBOM attestation; OpenSSF Scorecard; optional SLSA Build L3 via GitHub provenance.

**Accessibility:** `axe-core`, `pa11y-ci`, Lighthouse CI for Section 508 / WCAG 2.1 AA. All free/OSS.

**Governance:** NIST `oscal-cli` (or the `oscal` PyPI package, released 2026-07-14, with air-gapped offline validation) validating an **OSCAL 1.1.3** component-definition. All free/OSS.

**Dev ergonomics:** devcontainer, Docker Compose (local only), `justfile`, seeded demo data, one-command no-API-key demo (`just demo`).

## FREE / NO-CARD VERIFICATION TABLE (audited with primary sources)

| Component | Free forever | Card required | Account required | Relevant limits / notes | Replacement if it fails |
|---|---|---|---|---|---|
| Local inference (Ollama 0.19+/MLX/LM Studio) | Yes | No | No | Bounded only by M4 RAM/throughput | n/a (primary) |
| Groq free tier | Yes | No | Yes (email/Google/GitHub) | 30 RPM, 6,000 TPM, 14,400 RPD per model, org-level; cached tokens excluded; Batch API not on free tier | Local-only; escalate less |
| Cloudflare Pages (primary reviewer URL) | Yes | No | Yes | Per Cloudflare Pages Limits docs: build up to 500×/month, 20,000 files/site, 25 MiB/file, 20-min build timeout, unlimited bandwidth + unlimited preview deploys | GitHub Pages |
| GitHub Pages | Yes | No | Yes | Static hosting on public repo | Cloudflare Pages |
| GitHub Actions (public repo) | Yes | No | Yes | Unlimited minutes on public repos (2,000/mo only applies to private) | Run CI locally via `just ci` |
| CodeQL / secret scanning / Dependabot (public repo) | Yes | No | Yes | Free/enabled by default on public repos; GHAS license needed only for private | Semgrep + gitleaks locally |
| SQLite / DuckDB / Parquet | Yes | No | No | File-based; commit artifacts <25 MiB else use a Release asset | n/a |
| Hugging Face Spaces (optional live fallback) | Yes | No | Yes | Free CPU Space (2 vCPU/16 GB); sleeps after 48h inactivity; no card to start | Static-only; drop live demo |
| Render / Fly.io / Railway / Vercel live backends | — | Yes (card) | Yes | Require a card | **Dropped — ship static-only** |
| Inspect AI, promptfoo | Yes | No | No | MIT/OSS | n/a |
| syft, cosign/Sigstore, Scorecard, Semgrep, gitleaks, osv-scanner, pip-audit | Yes | No | No | OSS; Sigstore keyless uses GitHub OIDC, no card | n/a |
| pa11y-ci, axe-core, Lighthouse CI | Yes | No | No | OSS | n/a |
| Renovate | Yes | No | Yes (GitHub app) | Free for public repos | Dependabot |
| oscal-cli / oscal (PyPI) | Yes | No | No | OSS; offline validation | in-repo JSON-schema validation |
| OpenSanctions bulk data | Yes (non-commercial) | No | No (no key for bulk) | **CC-BY-NC 4.0 — non-commercial only, no sign-up/key for the bulk download.** Fine for this portfolio artifact; a production Treasury deployment would require a commercial data license. Attribution required. | GLEIF + OFAC direct join (see docs/ENTITY_RESOLUTION.md) |
| GLEIF Golden Copy / Concatenated files | Yes | No | No | Open data; RR-CDF 2.1; Level 2 relationship records ~658,145 (concatenated file dated 2026-07-08); Golden Copy published 3×/day, concatenated daily | n/a |
| OFAC Sanctions List Service | Yes | No | No | GET only; **User-Agent header REQUIRED (403 without)**; no key; files SDN_ADVANCED.XML, CONS_ADVANCED.XML, SDN.CSV, CONS_PRIM.CSV | OpenSanctions OFAC mirror |
| Federal Register API v1 | Yes | No | No | No key; per_page max 1000; can paginate only first 2000 results (use date filters for more) | govinfo bulk FR XML |
| eCFR API + govinfo bulk XML | Yes | No | No | No key; Title 31 bulk XML at govinfo (T31 rebuilt 2026-05-07 per bulk listing); set Accept header or get 406 | n/a |
| Treasury Fiscal Data API | Yes | No | No | No key; no documented rate limit (throttle politely) | n/a |

**Net zero-cost verdict:** the entire build is achievable with no card anywhere, including the drop of Postgres, Dagster, hosted observability, and all card-backed live-backend hosts. The single licensing caveat to disclose prominently is OpenSanctions' CC-BY-NC (non-commercial) term — acceptable for a portfolio artifact, flagged in README and the data card.
