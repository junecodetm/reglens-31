# Repository Structure, Architecture & Data Flow

> Decomposed from CLAUDE.md §4 and §8 (2026-07-28).

## Repository structure

```
reglens-31/
  CLAUDE.md
  README.md
  LICENSE              # code: Apache-2.0
  DATA_LICENSE.md      # outputs/data provenance & CC-BY-NC attribution for OpenSanctions
  justfile
  pyproject.toml       # uv, ruff, pyright config
  uv.lock
  .python-version
  .devcontainer/
  docker-compose.yml   # local only
  .claude/
    settings.json
    skills/
    agents/
    hooks/
  .github/workflows/   # ci.yml, security.yml, deploy-pages.yml, eval.yml
  reglens/
    __init__.py
    config.py          # pydantic-settings typed config
    ingest/            # federal_register.py, ecfr.py, ofac.py, gleif.py, allowlist.py, snapshot.py
    extract/           # llm.py (provider adapters), schema.py, prompts/
    provenance.py      # verify_span (fail-closed)
    graph/             # ownership.py (OFAC 50% rule; seeded Deripaska case)
    resolve/           # entity_resolution.py (opensanctions.py + splink/rapidfuzz fallback)
    eval/              # tasks.py (Inspect), gold/ (labeled set), metrics.py (Wilson, bootstrap)
    store/             # sqlite.py, duckdb.py, parquet.py, migrations/
    api/               # FastAPI /v1 (local dev only)
  web/                 # Next.js static export
  data/
    raw/<sha256>/      # content-addressed immutable snapshots
    fixtures/          # cached eval fixtures ($0 CI)
    processed/         # parquet
  governance/          # component-definition.json (OSCAL 1.1.3), model_card.md, data_card.md,
                       # ai_impact_assessment.md, monitoring_plan.md, rollback_plan.md
  scripts/             # check_zero_cost.py, redact_pii.py
  docs/
```

## Architecture & data flow

```
[Federal Register API] [eCFR/govinfo XML T31] [OFAC SLS XML] [GLEIF Golden Copy]
        \            |                 |                     /
         v           v                 v                    v
      ingest/snapshot.py  -> data/raw/<sha256>/ (content-addressed, immutable)
                         |
                         v
   extract/llm.py (local model, temp=0, JSON-schema constrained)
                         |
                         v
   provenance.py verify_span()  --(fail)-->  rejected_claims (counted, shown)
                         | (pass)
                         v
   store/ -> SQLite (records) + DuckDB/Parquet (analytics)
             |                          \
             v                           v
   graph/ownership.py (OFAC 50% rule + GLEIF L2 join, seeded case)
             |
             v
   Next.js static export (pre-computed) -> Cloudflare Pages (reviewer URL)
             ^
             |
   eval/ (Inspect AI over gold set, CI gate on cached fixtures, $0)
```

Data-flow rules: raw snapshots immutable and content-addressed; everything downstream derivable and reproducible; the deployed site is a **pre-computed static artifact** so the reviewer never depends on a live backend or an API key. Data versioning/lineage = the `<sha256>` snapshot directories + a `manifest.json` recording source id, URL, fetch time, and hash per run; schema evolution for ingested sources handled by versioned pydantic models with a `schema_version` field and a tolerant parser that logs unknown fields; idempotency = re-running a step on the same input SHA is a no-op.
