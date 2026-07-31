# Repository Structure, Architecture & Data Flow

> The tree below describes what exists; deliberately de-scoped modules are
> listed at the end of the section with their design records.

## Repository structure

```
reglens-31/
  CLAUDE.md
  README.md
  LICENSE              # code: Apache-2.0
  DATA_LICENSE.md      # outputs/data provenance & licence terms
  justfile
  pyproject.toml       # uv, ruff, pyright config
  uv.lock
  .claude/             # settings.json, skills/, agents/, hooks/
  .github/workflows/   # ci.yml, security.yml, deploy-pages.yml, eval.yml
  functions/           # Cloudflare Pages Function: /api/draft live narrative
                       # endpoint (same-origin proxy; the only server-side code)
  reglens/
    config.py          # pydantic-settings typed config
    corpus.py          # canonical corpus scope: inclusion rule + extraction-sample rule
    currency.py        # eCFR section census vs amendment dates -> drift vs the pinned date
    memo.py            # per-part review memoranda: deterministic evidence + gated narrative
    provenance.py      # verify_span (fail-closed)
    structure.py       # typed CFR section-structure parser
    search_index.py    # BM25-style index builder for the static site
    use_case_inventory.py
    ingest/            # federal_register.py, ecfr.py, ecfr_versions.py, uscode.py,
                       # references.py, inventory.py, allowlist.py, snapshot.py
    extract/           # llm.py (provider adapter + transport), chunk.py, schema.py,
                       # records.py, run.py, prompts/
    api/               # schemas.py (response models), spec.py (OpenAPI 3.1 from
                       # pydantic — no web framework, no server; see below)
    authority/         # citations -> USLM resolution -> classification
    grounding/         # two-sided marker retrieval (deterministic)
    draft/             # DDH skeletons over the full part/doc-type grid, narrative
                       # (local or Groq provider), conformance gates
    eval/              # harness.py, ogc01.py, metrics.py (Wilson, bootstrap, kappa),
                       # provisions.py, adjudicate.py, gold/
    store/             # database.py (SQLite + DuckDB/Parquet), corpus_scope.py,
                       # export_web.py, export_api.py
  web/                 # Next.js static export (app/, public/data/ + public/api/v1/
                       # generated artifacts)
  tests/               # pytest suite + .mts/.mjs web contract tests
  data/
    raw/<sha256>/      # content-addressed immutable snapshots
    processed/         # claims.json, parquet, authority/grounding/conformance artifacts
  governance/          # model_card.md, data_card.md, ai_impact_assessment.md,
                       # monitoring_plan.md, rollback_plan.md
  scripts/             # check_zero_cost.py, redact_pii.py
  docs/
```

**Deliberately out of scope** (decision record: docs/CHECKLIST.md):
`reglens/graph/` (OFAC 50% ownership), `reglens/resolve/` (entity resolution),
`store/migrations/` (schema is created inline by `store/database.py`), and
`governance/component-definition.json` (OSCAL). The eval harness is a custom
implementation in `reglens/eval/`, not an Inspect AI wrapper.

**FastAPI was considered and not adopted.** The original design called for a FastAPI `/v1`
surface for local development. What shipped is `reglens/api/` + `store/export_api.py`:
the same pydantic models, materialized as static JSON under `web/public/api/v1/` with a
generated OpenAPI 3.1 document. *Why the plan changed:* the reviewer must never depend on
a running service (CLAUDE.md §21), so a server could only ever have been a second, local
transport for data the static export already had to produce — and a second transport is a
second thing that can disagree with the pages. Deriving the API from the site's own
exported artifacts makes "the API serves what the pages show" structural instead of
aspirational, keeps the runtime dependency list at five packages, and costs nothing to
host. The trade-off, stated plainly: there is no query interface — filtering and
pagination are materialized at build time, so a consumer wanting a different page size
must re-run the exporter rather than pass a parameter.

**The one server-side exception: the live drafting endpoint.** `functions/api/draft.ts`
is a Cloudflare Pages Function (free plan, no card) behind the same-origin route
`/api/draft`. It exists so the Drafting Assistant can accept parameters — part, rule
type, an optional policy objective — and return a freshly generated opening narrative,
which the client splices into the exporter's own sentinel-slotted skeleton template and
checks with an in-browser subset of the conformance gate (`web/app/components/
draft-live.ts`). It does not weaken the static-first doctrine, by construction: every
page renders fully with the endpoint absent, the client falls back to the committed,
fully gated drafts on any failure (including free-tier quota exhaustion), CSP
`connect-src 'self'` is unchanged because the browser never talks to a third party, and
the Groq key exists only as a Pages project secret. The reviewer *may* use the live
endpoint; nothing the reviewer sees *depends* on it. Threat model: docs/SECURITY.md.

## Architecture & data flow

```
[Federal Register API]  [eCFR Title 31]  [OLRC U.S. Code USLM]  [reference PDFs]
         \                    |                   |                   /
          v                   v                   v                  v
      ingest/snapshot.py  -> data/raw/<sha256>/ (content-addressed, immutable)
                         |
                         v
   corpus.py in_extraction_sample()  --(not sampled)-->  ingested, not extracted
                         | (sampled)
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
 authority/          grounding/           draft/ (part x doc-type grid;
 (citations ->       (two-sided           narratives via the configured
  USLM -> class)      markers)            provider; fail-closed gates)
      \                  |                  |
       +--------+--------+                  |
                v                           |
   memo.py (per-part review memoranda:      |
   deterministic evidence + gated           |
   model narrative)                         |
                \                           /
                 v                         v
   store/export_web.py -> web/public/data/ (pre-computed static artifacts,
                          incl. sentinel-slotted draft templates)
                         |            |
                         |            +-> currency.py -> currency.json (drift vs eCFR)
                         v
   store/export_api.py -> web/public/api/v1/ (same data, typed + OpenAPI 3.1)
                         |
                         v
   Next.js static export -> Cloudflare Pages (reviewer URL)
                         |
                         +-> functions/api/draft.ts (optional live narrative;
                             browser splices it into the exported skeleton
                             template and runs the in-browser gate subset;
                             any failure falls back to the committed drafts)
                         ^
                         |
   eval/ (custom harness over the gold set; CI regression gate, offline, $0)
```

Data-flow rules: raw snapshots immutable and content-addressed; everything downstream derivable and reproducible; the deployed site is a **pre-computed static artifact** so the reviewer never depends on a live backend or an API key. Data versioning/lineage = the `<sha256>` snapshot directories + a `manifest.json` recording source id, URL, fetch time, and hash per run; schema evolution for ingested sources handled by versioned pydantic models with a `schema_version` field and a tolerant parser that logs unknown fields.

**Scope is stated twice, and both statements are code.** `reglens/corpus.py` holds the
*inclusion* rule (which Federal Register documents the corpus contains) and the
*extraction-sample* rule (`in_extraction_sample`: the five 31 CFR part texts plus every
in-scope document published in `EXTRACTION_YEAR`). Every in-scope document is ingested and
committed; the model is run over the sample, because inference is local-only. `site.json`
and `/api/v1/index.json` both publish `documents_extracted` against `documents_in_scope`
from one function (`store/corpus_scope.py::build_corpus`), and `tests/test_corpus.py`
asserts the persisted claim set is exactly what the rule selects — so the sample cannot
drift into "whichever documents were run first" without a test failing.

**Idempotency.** Re-running extraction on an unchanged corpus is a no-op: a document is reused only when its source SHA and every persisted claim's run record — model tag, prompt hash, input hash, temperature, inference runtime version, and chunk-plan hash — match what the current provider would produce. Any change to model, prompt, runtime or chunking invalidates the cache automatically, and `--force` re-extracts the selection unconditionally. The runtime version is part of the record because an Ollama upgrade silently changed structured-output behaviour once (see `reglens/extract/llm.py::generation_schema`), which a model-tag-only record could not distinguish from a model change. The chunk-plan hash is part of it for the same class of reason: the model reads one chunk at a time, so where the boundaries fall is a real input to the output, and a record naming only the text could not distinguish a re-chunked run from an identical one. A record predating either field carries `"unknown"`, which can never match a computed value, so such a document is re-extracted rather than trusted.
