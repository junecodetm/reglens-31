# Full Command Surface

> Implemented in the repo-root `justfile`; every recipe below is built and runnable.

```
just setup        # uv sync, install web deps, pull the pinned local model
just demo         # one-command, no-API-key, offline demo (seeded data) -> opens static site
just ingest       # snapshot named Federal Register documents / eCFR parts into data/raw/<sha>
just ingest-corpus # close the corpus: every FR final rule amending an in-scope part
just ecfr-currency # refresh the eCFR section census + amendment dates (drift baseline)
just extract      # local extraction + provenance gate over the sampled documents -> parquet
                  #   (sample rule: reglens.corpus.in_extraction_sample; --all for everything)
just rebuild      # everything downstream of claims.json in dependency order, then the site
                  #   (use after any extraction, including one launched detached)
just authority    # authority citations -> USLM resolution -> classification
just grounding    # two-sided grounding-marker retrieval (deterministic)
just draft        # DDH skeletons + conformance gates over the full part/doc-type grid
                  #   (narratives from the configured provider; unchanged drafts reused)
just memo         # per-part review memoranda: deterministic evidence + gated model narrative
just eval         # eval harnesses (core + OGC-01) -> metrics + Wilson/bootstrap CIs ($0)
just build-web    # export site data + static read API (web/public/api/v1) + Next.js -> web/out
just ci           # full CI locally (lint, type, test, security, a11y, eval gate)
just security     # semgrep, zero-cost allow-list, PII scan (dependency audits run in CI)
just a11y         # pa11y (WCAG2AA) against web/out
just check-cost   # scripts/check_zero_cost.py (fails if a non-allowlisted service appears)
```

De-scoped capabilities (OFAC 50% ownership graph, OSCAL validation) have no
recipes; the de-scope record lives in `docs/CHECKLIST.md`.
