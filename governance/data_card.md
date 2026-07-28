# Data Card — RegLens-31 Snapshots & Gold Set

## Sources (complete list for this build)
- Federal Register API v1 — 20 most recent Treasury final rules at snapshot time (public domain).
- eCFR versioner API, Title 31 parts 50, 223, 285, 356, 501 at a pinned point-in-time date (U.S. Government work; unofficial compilation).

All fetches pass the runtime allow-list (`reglens/ingest/allowlist.py`); the exclusion list (BSA/SAR, FinCEN BOI, taxpayer data, private PII, authed/paywalled content) is enforced there and scanned in CI.

## Provenance & versioning
Raw snapshots are immutable and content-addressed (`data/raw/<sha256>/` + manifest: source id, URL, fetch time, hash). Derived claims and eval fixtures are reproducible from snapshots + pinned model + temperature 0 + fixed seed.

## Gold set
251 provisions sampled deterministically (seeded) in two disclosed strata (recorded per record as `stratum`): (1) `base` — 7 paragraphs per document across all 25 documents; (2) `ecfr-supplement` — additional paragraphs from the operative eCFR parts (obligation-dense) to strengthen the positive class. Pooled precision therefore mixes strata with different selection rates; per-stratum metrics ship in `eval.json`.

Labels follow `docs/ANNOTATION_GUIDELINES.md` and were proposed by **two frozen, independent passes of two different models** — pass 1 `claude-fable-5`, pass 2 `claude-sonnet-5` (`proposed_by` recorded per record; frozen in `pass1.jsonl`/`pass2.jsonl` so later adjudication cannot contaminate the agreement statistic). Cross-model Cohen's kappa on `is_obligation`: reported in `eval.json` with its Landis-Koch band. A same-model repeat pass was also run and discarded as uninformative: at temperature-controlled settings the same model reproduces its own labels (agreement 1.0), which measures determinism, not reliability.

Labels are **not ground truth until human-adjudicated** — every record carries `adjudicated: false` until then, and all published metrics carry the Provisional label.
