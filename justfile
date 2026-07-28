# RegLens-31 command surface — docs/COMMANDS.md
# Stubbed recipes exit 1 with a pointer to their build phase (docs/BUILD_PLAN.md).

# uv sync + pull the pinned local model
setup:
    uv sync
    ollama pull qwen3:8b

# one-command, no-API-key, offline demo (seeded data) -> opens static site
demo:
    @echo "TODO(Phase 0): offline demo on seeded data" && exit 1

# snapshot Federal Register + eCFR T31 + OFAC + GLEIF into data/raw/<sha>
ingest:
    @echo "TODO(Phase 1): reglens.ingest snapshots (allow-list enforced)" && exit 1

# run local extraction + provenance gate -> parquet
extract:
    @echo "TODO(Phase 1): reglens.extract + provenance.verify_span" && exit 1

# build OFAC 50% ownership graph (seeded Deripaska case guaranteed)
graph:
    @echo "TODO(Phase 4): reglens.graph.ownership" && exit 1

# Inspect AI harness over gold set -> metrics + Wilson CIs (fixtures, $0)
eval:
    @echo "TODO(Phase 3): inspect eval over gold set/fixtures" && exit 1

# Next.js static export -> web/out
build-web:
    @echo "TODO(Phase 2): next build (output: export)" && exit 1

# full CI locally (lint, type, test, security, a11y, eval gate)
ci: check-cost
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest

# pip-audit, osv-scanner, gitleaks, semgrep, syft SBOM
security:
    @echo "TODO(Phase 5): pip-audit, osv-scanner, gitleaks, semgrep, syft" && exit 1

# pa11y-ci + axe + lighthouse against web/out
a11y:
    @echo "TODO(Phase 2): pa11y-ci + axe + lighthouse" && exit 1

# oscal-cli validate governance/component-definition.json
govern:
    @echo "TODO(Phase 4): oscal-cli validate governance/component-definition.json" && exit 1

# scripts/check_zero_cost.py (fails if a non-allowlisted service appears)
check-cost:
    @python3 scripts/check_zero_cost.py
