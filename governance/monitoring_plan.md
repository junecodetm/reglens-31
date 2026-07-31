# Monitoring Plan — RegLens-31

The deployed artifact is a precomputed static export. Monitoring consists of
snapshot refresh, validation, and retirement controls rather than live
telemetry.

- **Staleness:** The site footer displays the source snapshot date. A snapshot
  older than 90 days requires either a refresh through `just ingest-corpus`,
  `just ecfr-currency`, `just extract`, and `just rebuild`, or retirement of
  the demonstration with a dated notice. `just rebuild` regenerates the
  database, authority, grounding, draft, memorandum, evaluation, and web
  artifacts. `docs/COMMANDS.md` documents the command surface.
- **Schema drift:** Pydantic validation reports upstream schema changes during
  ingestion. The tolerant parser logs unknown fields; hard validation failures
  stop the pipeline.
- **Quality regression:** The CI evaluation gate runs against committed
  fixtures on every push. F1 below the baseline minus 0.05 or citation fidelity
  below 1.0 fails the build.
- **Security cadence:** A weekly workflow runs CodeQL, pip-audit, osv-scanner,
  gitleaks, and semgrep, and generates an SBOM.
- **Adjudication cadence:** Review sessions cover approximately 20 evaluation
  items under `docs/ADJUDICATE.md`. Metrics and
  `Provisional — machine-proposed labels, human-adjudicated: N/M` are
  recalculated from the JSONL records.
