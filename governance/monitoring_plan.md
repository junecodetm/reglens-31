# Monitoring Plan — RegLens-31

The deployed artifact is a pre-computed static export; "monitoring" is therefore snapshot-refresh discipline, not live telemetry.

- **Staleness trigger:** the site footer shows the snapshot's "data as of" date. Policy: refresh (re-run `just ingest && just extract && just eval && just build-web`, commit, push → auto-deploy) when the snapshot is older than 90 days, or retire the demo with a dated notice.
- **Drift trigger:** any upstream schema change surfaces as pydantic validation failures at ingest (tolerant parser logs unknown fields; hard failures stop the pipeline fail-closed).
- **Quality regression:** the CI eval gate re-runs the harness on every push from committed fixtures; F1 below baseline − 0.05 or citation fidelity < 1.0 fails the build.
- **Security cadence:** weekly scheduled security workflow (CodeQL, pip-audit, osv-scanner, gitleaks, semgrep, SBOM).
- **Adjudication cadence:** ~20 gold items per evening (`docs/ADJUDICATE.md`); metrics and their provisional label restate automatically from the JSONL.
