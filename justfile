# RegLens-31 command surface — docs/COMMANDS.md
# Stubbed recipes exit 1 with a pointer to their build phase (docs/BUILD_PLAN.md).

# uv sync + pull the pinned local model
setup:
    uv sync
    ollama pull qwen3:8b

# one-command, no-API-key, offline demo (seeded data) -> opens static site
demo:
    @echo "TODO(Phase 0): offline demo on seeded data" && exit 1

# snapshot Federal Register documents into data/raw/<sha> (allow-list enforced)
ingest *docs:
    uv run python -m reglens.ingest {{docs}}

# run local extraction + provenance gate over all snapshots
extract:
    uv run python -m reglens.extract

# build OFAC 50% ownership graph (seeded Deripaska case guaranteed)
graph:
    @echo "TODO(Phase 4): reglens.graph.ownership" && exit 1

# eval harness over the gold set -> metrics + Wilson/bootstrap CIs ($0, offline)
eval:
    uv run python -m reglens.eval.harness

# eval regression gate (CI): fails on F1 regression or fidelity < 1.0
eval-gate:
    uv run python -m reglens.eval.harness --gate

# export data for the UI + Next.js static export -> web/out
build-web:
    uv run python -m reglens.store.export_web
    cd web && npm run build

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
