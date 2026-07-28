# Data Card — RegLens-31 Snapshots & Gold Set

## Sources (complete list for this build)
- Federal Register API v1 — 20 most recent Treasury final rules at snapshot time (public domain).
- eCFR versioner API, Title 31 parts 50, 223, 285, 356, 501 at a pinned point-in-time date (U.S. Government work; unofficial compilation).

All fetches pass the runtime allow-list (`reglens/ingest/allowlist.py`); the exclusion list (BSA/SAR, FinCEN BOI, taxpayer data, private PII, authed/paywalled content) is enforced there and scanned in CI.

## Provenance & versioning
Raw snapshots are immutable and content-addressed (`data/raw/<sha256>/` + manifest: source id, URL, fetch time, hash). Derived claims and eval fixtures are reproducible from snapshots + pinned model + temperature 0 + fixed seed.

## Gold set
251 provisions sampled deterministically (seeded) in two disclosed strata: (1) 7 paragraphs per document across all 25 documents; (2) a supplement from the operative eCFR parts (obligation-dense) to strengthen the positive class. Labels follow `docs/ANNOTATION_GUIDELINES.md`, were proposed by two independent passes of a frontier model (`proposed_by` recorded per record), and are **not ground truth until human-adjudicated** — every record carries `adjudicated: false` until then, and all published metrics carry the Provisional label. Known limitation: inter-pass agreement between two runs of the same model overstates human inter-annotator agreement.
