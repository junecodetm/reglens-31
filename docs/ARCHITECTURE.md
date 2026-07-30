# Repository Structure, Architecture & Data Flow

> Decomposed from CLAUDE.md §4 and §8 (2026-07-28). Tree corrected 2026-07-30 to describe
> what exists: the original was the *planned* layout and listed five modules and two files
> that were never built (see "Planned but not built" below).

## Repository structure

```
reglens-31/
  CLAUDE.md
  README.md
  LICENSE              # code: Apache-2.0
  DATA_LICENSE.md      # outputs/data provenance & licence terms
  BUILD.md             # single-pass build execution prompt (process-transparency artifact)
  EXTEND-OGC01.md      # OGC-01 extension spec: authority/grounding/draft stages
  justfile
  pyproject.toml       # uv, ruff, pyright config
  uv.lock
  .claude/             # settings.json, skills/, agents/, hooks/
  .github/workflows/   # ci.yml, security.yml, deploy-pages.yml, eval.yml
  reglens/
    config.py          # pydantic-settings typed config
    corpus.py          # canonical corpus scope + inclusion rule
    provenance.py      # verify_span (fail-closed)
    structure.py       # typed CFR section-structure parser
    search_index.py    # BM25-style index builder for the static site
    use_case_inventory.py
    ingest/            # federal_register.py, ecfr.py, uscode.py, references.py,
                       # inventory.py, allowlist.py, snapshot.py
    extract/           # llm.py (provider adapter + transport), chunk.py, schema.py,
                       # records.py, run.py, prompts/
    authority/         # EXTEND-OGC01 Stage 1: citations -> USLM resolution -> classification
    grounding/         # EXTEND-OGC01 Stage 2: two-sided marker retrieval (deterministic)
    draft/             # EXTEND-OGC01 Stage 3: DDH skeletons, narrative, conformance gates
    eval/              # harness.py, ogc01.py, metrics.py (Wilson, bootstrap, kappa),
                       # provisions.py, adjudicate.py, gold/
    store/             # database.py (SQLite + DuckDB/Parquet), export_web.py
  web/                 # Next.js static export (app/, public/data/ generated artifacts)
  tests/               # pytest suite + .mts/.mjs web contract tests
  data/
    raw/<sha256>/      # content-addressed immutable snapshots
    processed/         # claims.json, parquet, authority/grounding/conformance artifacts
  governance/          # model_card.md, data_card.md, ai_impact_assessment.md,
                       # monitoring_plan.md, rollback_plan.md
  scripts/             # check_zero_cost.py, redact_pii.py
  docs/
```

**Planned but not built** (deliberate, sanctioned de-scopes — see docs/CHECKLIST.md):
`reglens/graph/` (OFAC 50% ownership), `reglens/resolve/` (entity resolution),
`reglens/api/` (FastAPI dev surface), `store/migrations/` (schema is created inline by
`store/database.py`), and `governance/component-definition.json` (OSCAL). The eval harness
is a custom implementation in `reglens/eval/`, not an Inspect AI wrapper.

## Architecture & data flow

```
[Federal Register API]  [eCFR Title 31]  [OLRC U.S. Code USLM]  [reference PDFs]
         \                    |                   |                   /
          v                   v                   v                  v
      ingest/snapshot.py  -> data/raw/<sha256>/ (content-addressed, immutable)
                         |
                         v
   extract/llm.py (local model, temp=0, seed=31, JSON-schema constrained)
                         |
                         v
   provenance.py verify_span()  --(fail)-->  rejected_claims (counted, shown)
                         | (pass)
                         v
   store/database.py -> SQLite (records) + DuckDB/Parquet (analytics)
                         |
      +------------------+------------------+
      v                  v                  v
 authority/          grounding/           draft/
 (citations ->       (two-sided           (DDH skeletons +
  USLM -> class)      markers)             conformance gates)
      \                  |                  /
       v                 v                 v
   store/export_web.py -> web/public/data/ (pre-computed static artifacts)
                         |
                         v
   Next.js static export -> Cloudflare Pages (reviewer URL)
                         ^
                         |
   eval/ (custom harness over the gold set; CI regression gate, offline, $0)
```

Data-flow rules: raw snapshots immutable and content-addressed; everything downstream derivable and reproducible; the deployed site is a **pre-computed static artifact** so the reviewer never depends on a live backend or an API key. Data versioning/lineage = the `<sha256>` snapshot directories + a `manifest.json` recording source id, URL, fetch time, and hash per run; schema evolution for ingested sources handled by versioned pydantic models with a `schema_version` field and a tolerant parser that logs unknown fields.

**Idempotency.** Re-running extraction on an unchanged corpus is a no-op: a document is reused only when its source SHA and every persisted claim's run record — model tag, prompt hash, input hash, temperature, and inference runtime version — match what the current provider would produce. Any change to model, prompt or runtime invalidates the cache automatically, and `--force` re-extracts unconditionally. The runtime version is part of the record because an Ollama upgrade silently changed structured-output behaviour once (see `reglens/extract/llm.py::generation_schema`), which a model-tag-only record could not distinguish from a model change.
