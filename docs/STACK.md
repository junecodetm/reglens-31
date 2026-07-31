# Audited Zero-Cost Tech Stack + Free/No-Card Verification Table

> Enforcement: this file's free/no-card table is the allow-list for the ZERO-COST INVARIANT (CLAUDE.md §2, invariant 1).

**Language / tooling:** Python 3.13 with `uv` (env + lock), `ruff` (lint+format), `pyright` (types), `pydantic` v2 (schemas). *Justification:* fast, reproducible, typed, all free/OSS.

**Inference (local-first, hybrid):**
- **Primary: local on an Apple M4 (16 GB) via Ollama, pinned model `qwen3:8b`** at temperature 0, seed 31, `num_ctx` 16384, with JSON-schema adherence enforced through Ollama's structured-output `format` parameter. *Justification:* no card, no egress, aligns with M-25-21's "less data and compute." Machines with more unified memory can substitute a larger model tag; the determinism record (model tag + runtime version) invalidates cached extractions automatically on any change. *Honest caveat:* full-document field accuracy is still hard for all local extraction models — which is exactly why the provenance gate + eval harness exist.
- **Secondary: Groq free tier for the generative draft stages.** Extraction — the evidentiary core — is local-only, always. The short generative stages (draft narratives, review-memo narratives, and the live drafting endpoint) use the Groq free tier with the pinned `openai/gpt-oss-120b` at temperature 0, seed 31, schema-constrained server-side. No credit card; limits are org-level (multiple keys do not bypass them) and, as measured against this key's response headers, 1,000 requests/day and 8,000 tokens/min for this model — and free-tier admission *reserves* `max_completion_tokens` against the per-minute budget, so requests keep small caps and retry on 429 honoring `Retry-After`. The card-gated Developer tier ("up to 10x higher limits" + 25% token discount) is **prohibited** by invariant #1. *Workload check:* the full draft grid plus memoranda is ~15 requests of a few hundred tokens each; the live endpoint sends one bounded request per visitor action and degrades to the committed drafts on 429.
- **Adapter pattern (implemented):** `chat_json` (local) and `chat_json_openai` (Groq) in `reglens/extract/llm.py`; `REGLENS_DRAFT_PROVIDER` selects the generative-stage provider, every dossier records which one produced each artifact, and a bare rebuild reuses unchanged artifacts so the repo builds fully offline with no key.

**Storage:** SQLite (system of record for small structured tables) + DuckDB (analytics, joins over Parquet) + Parquet artifacts committed to the repo (or to a GitHub Release asset if >25 MiB). *Justification:* Postgres was considered and dropped — it needs a card-backed host; SQLite/DuckDB are zero-infra, and DuckDB is the stronger fit for an analytics-shaped join workload. Alembic was likewise not adopted (overkill without a server DB).

**Orchestration:** plain, typed Python modules invoked by `just` locally and by GitHub Actions remotely, with idempotent, content-addressed steps. *Justification:* Dagster was considered and not adopted — heavy for a solo build; a clean functional pipeline is easier to finish and audit.

**API / UI:** a static read API under `web/public/api/v1/` with a generated OpenAPI 3.1 document (FastAPI was considered and not adopted — reasoning in docs/ARCHITECTURE.md); Next.js `output: 'export'` static site + `@trussworks/react-uswds` (React USWDS 3 component library, Apache-2.0) on React 19. Micro-interactions via GSAP (`gsap` + `@gsap/react`): 100% free — including all formerly-paid Club plugins — since 2025-04-30 under the GreenSock Standard License (free but not OSS; public static-site use explicitly permitted; no card, no account); all motion is gated behind `gsap.matchMedia` so `prefers-reduced-motion` users get the final state. Design-quality tooling via `impeccable` (Apache-2.0, pinned devDependency): dev-time skill + deterministic detector CLI only, never shipped in the site bundle.

**Evaluation:** a custom harness in `reglens/eval/` (`harness.py`, `ogc01.py`, `metrics.py`). Inspect AI was considered and not adopted: the only Inspect features this build needed were bootstrap aggregation and F1 scoring, and the project already had to own Wilson intervals and a rule-clustered bootstrap in `reglens/eval/metrics.py` (docs/EVALUATION.md) because those are not native to Inspect — wrapping a dependency around code that still had to exist added a dependency without removing any. The trade-off, stated plainly: the harness is less externally recognisable to a reviewer who knows Inspect, and it carries no third-party validation of the harness itself — the statistics are unit-tested in-repo instead. `promptfoo` was likewise not adopted. Both remain zero-cost options if the harness ever needs to be portable.

**Observability:** `structlog` structured JSON logs + per-run manifests recording model tag, prompt hash, input SHA and inference runtime version. *Justification:* hosted observability (Langfuse/Phoenix) was considered and dropped — self-hosting is free but is another service to babysit; file-based telemetry is zero-cost and air-gap-friendly.

**DevSecOps (all free/OSS on PUBLIC repos):** SHA-pinned least-privilege GitHub Actions; Renovate (free GitHub app on public repos); `pip-audit`; `osv-scanner`; `gitleaks`; CodeQL code scanning (free on public repos; GHAS only needed for private); Semgrep (free CLI + community rules); CycloneDX SBOM via `syft`; distroless/Chainguard-Wolfi base images for any container; signed commits; `cosign` keyless (Sigstore, OIDC via GitHub — no card) signing + SBOM attestation; OpenSSF Scorecard; optional SLSA Build L3 via GitHub provenance.

**Accessibility:** `axe-core`, `pa11y-ci`, Lighthouse CI for Section 508 / WCAG 2.1 AA. All free/OSS.

**Governance:** NIST `oscal-cli` (or the `oscal` PyPI package, released 2026-07-14, with air-gapped offline validation) validating an **OSCAL 1.1.3** component-definition. All free/OSS.

**Dev ergonomics:** devcontainer, Docker Compose (local only), `justfile`, seeded demo data, one-command no-API-key demo (`just demo`).

## FREE / NO-CARD VERIFICATION TABLE (audited with primary sources)

| Component | Free forever | Card required | Account required | Relevant limits / notes | Replacement if it fails |
|---|---|---|---|---|---|
| Local inference (Ollama 0.19+/MLX/LM Studio) | Yes | No | No | Bounded only by M4 RAM/throughput | n/a (primary) |
| Groq free tier | Yes | No | Yes (email/Google/GitHub) | Org-level; measured for the pinned model: 1,000 RPD, 8,000 TPM (admission reserves the completion cap); Batch API not on free tier | Local-only generative stages; live endpoint 503s + falls back |
| Cloudflare Pages (primary reviewer URL) | Yes | No | Yes | Per Cloudflare Pages Limits docs: build up to 500×/month, 20,000 files/site, 25 MiB/file, 20-min build timeout, unlimited bandwidth + unlimited preview deploys | GitHub Pages |
| Cloudflare Pages Functions (live drafting endpoint) | Yes | No | Yes (same account) | Free plan: 100,000 requests/day; the endpoint is an optional enhancement — the site is fully functional without it | Static-only; committed drafts remain |
| GitHub Pages | Yes | No | Yes | Static hosting on public repo | Cloudflare Pages |
| GitHub Actions (public repo) | Yes | No | Yes | Unlimited minutes on public repos (2,000/mo only applies to private) | Run CI locally via `just ci` |
| CodeQL / secret scanning / Dependabot (public repo) | Yes | No | Yes | Free/enabled by default on public repos; GHAS license needed only for private | Semgrep + gitleaks locally |
| SQLite / DuckDB / Parquet | Yes | No | No | File-based; commit artifacts <25 MiB else use a Release asset | n/a |
| Hugging Face Spaces (optional live fallback) | Yes | No | Yes | Free CPU Space (2 vCPU/16 GB); sleeps after 48h inactivity; no card to start | Static-only; drop live demo |
| Render / Fly.io / Railway / Vercel live backends | — | Yes (card) | Yes | Require a card | **Dropped — ship static-only** |
| Inspect AI, promptfoo | Yes | No | No | MIT/OSS — **not adopted**; the eval harness is custom (`reglens/eval/`) | n/a |
| syft, cosign/Sigstore, Scorecard, Semgrep, gitleaks, osv-scanner, pip-audit | Yes | No | No | OSS; Sigstore keyless uses GitHub OIDC, no card | n/a |
| pa11y-ci, axe-core, Lighthouse CI | Yes | No | No | OSS | n/a |
| GSAP (`gsap` + `@gsap/react`) | Yes | No | No | 100% free incl. all formerly-Club plugins since 2025-04-30; GreenSock Standard License (free, not OSS) — public static-site use explicitly permitted; plain npm install | CSS transitions only |
| impeccable (design skill + detector, dev-time) | Yes | No | No | Apache-2.0; pinned devDependency; deterministic detector CLI runs offline in CI; never in the shipped bundle. Vendored skill scripts (`.claude/skills/impeccable/`) are excluded from the zero-cost URL scan (documented in `scripts/check_zero_cost.py`); its update phone-home is disabled via `updateCheck: false`, and its transitive puppeteer postinstall is blocked by `web/.npmrc` `ignore-scripts` | manual craft-floor checklist |
| Renovate | Yes | No | Yes (GitHub app) | Free for public repos | Dependabot |
| oscal-cli / oscal (PyPI) | Yes | No | No | OSS; offline validation | in-repo JSON-schema validation |
| OpenSanctions bulk data | Yes (non-commercial) | No | No (no key for bulk) | **CC-BY-NC 4.0 — non-commercial only, no sign-up/key for the bulk download.** Fine for this portfolio artifact; a production Treasury deployment would require a commercial data license. Attribution required. | GLEIF + OFAC direct join (see docs/ENTITY_RESOLUTION.md) |
| GLEIF Golden Copy / Concatenated files | Yes | No | No | Open data; RR-CDF 2.1; Level 2 relationship records ~658,145 (concatenated file dated 2026-07-08); Golden Copy published 3×/day, concatenated daily | n/a |
| OFAC Sanctions List Service | Yes | No | No | GET only; **User-Agent header REQUIRED (403 without)**; no key; files SDN_ADVANCED.XML, CONS_ADVANCED.XML, SDN.CSV, CONS_PRIM.CSV | OpenSanctions OFAC mirror |
| Federal Register API v1 | Yes | No | No | No key; per_page max 1000; can paginate only first 2000 results (use date filters for more) | govinfo bulk FR XML |
| eCFR API + govinfo bulk XML | Yes | No | No | No key; Title 31 bulk XML at govinfo (T31 rebuilt 2026-05-07 per bulk listing); set Accept header or get 406 | n/a |
| Treasury Fiscal Data API | Yes | No | No | No key; no documented rate limit (throttle politely) | n/a |

**Net zero-cost verdict:** the entire build is achievable with no card anywhere, including the drop of Postgres, Dagster, hosted observability, and all card-backed live-backend hosts. The single licensing caveat to disclose prominently is OpenSanctions' CC-BY-NC (non-commercial) term — acceptable for a portfolio artifact, flagged in README and the data card.
