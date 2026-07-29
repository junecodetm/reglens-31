# Full Command Surface

> Decomposed from CLAUDE.md §6 (2026-07-28). Implemented in the repo-root `justfile`; recipes not yet built are stubs that exit 1 with a phase pointer (see docs/BUILD_PLAN.md).

```
just setup        # uv sync, install pre-commit, pull local model
just demo         # one-command, no-API-key, offline demo (seeded data) -> opens static site
just ingest       # snapshot Federal Register + eCFR T31 + OFAC + GLEIF into data/raw/<sha>
just extract      # run local extraction + provenance gate -> parquet
just graph        # build OFAC 50% ownership graph (seeded Deripaska case guaranteed)
just authority    # EXTEND-OGC01: authority citations -> USLM resolution -> classification
just grounding    # EXTEND-OGC01: two-sided grounding-marker retrieval
just draft        # EXTEND-OGC01: DDH rule skeletons + conformance gates
just eval         # eval harnesses (core + OGC-01) -> metrics + Wilson/bootstrap CIs ($0)
just build-web    # Next.js static export -> web/out
just ci           # full CI locally (lint, type, test, security, a11y, eval gate)
just security     # pip-audit, osv-scanner, gitleaks, semgrep, syft SBOM
just a11y         # pa11y-ci + axe + lighthouse against web/out
just govern       # oscal-cli validate governance/component-definition.json
just check-cost   # scripts/check_zero_cost.py (fails if a non-allowlisted service appears)
```
