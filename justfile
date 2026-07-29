# RegLens-31 command surface — docs/COMMANDS.md
# Stubbed recipes exit 1 with a pointer to their build phase (docs/BUILD_PLAN.md).

# uv sync + web deps + pull the pinned local model
setup:
    uv sync
    cd web && npm install --no-audit --no-fund
    ollama pull qwen3:8b

# one-command, no-API-key, offline demo -> serves the static site
demo:
    @test -d web/out || just build-web
    @echo "RegLens-31 demo: http://localhost:8031 (Ctrl-C to stop)"
    python3 -m http.server 8031 -d web/out

# snapshot Federal Register documents into data/raw/<sha> (allow-list enforced)
ingest *docs:
    uv run python -m reglens.ingest {{docs}}

# run local extraction + provenance gate over all snapshots, then rebuild stores
extract:
    uv run python -m reglens.extract
    uv run python -m reglens.store.database

# OFAC 50% ownership graph — de-scoped from this build (docs/PROGRESS.md; first
# item in the sanctioned de-scope order). Design + caveats: docs/ENTITY_RESOLUTION.md.
graph:
    @echo "de-scoped: see docs/PROGRESS.md and docs/ENTITY_RESOLUTION.md" && exit 1

# EXTEND-OGC01 Stage 1: authority citations -> USLM resolution -> classification
authority:
    uv run python -m reglens.authority.run

# EXTEND-OGC01 Stage 2: two-sided grounding-marker retrieval (deterministic)
grounding:
    uv run python -m reglens.grounding.run

# EXTEND-OGC01 Stage 3: DDH skeletons + conformance gates (local model narrative)
draft:
    uv run python -m reglens.draft.run

# eval harness over the gold set -> metrics + Wilson/bootstrap CIs ($0, offline)
eval:
    uv run python -m reglens.eval.harness
    uv run python -m reglens.eval.ogc01

# eval regression gate (CI): fails on F1 regression or fidelity < 1.0
eval-gate:
    uv run python -m reglens.eval.harness --gate
    uv run python -m reglens.eval.ogc01 --gate

# export data for the UI + Next.js static export -> web/out
build-web:
    uv run python -m reglens.store.export_web
    # Stale incremental state breaks builds after route deletions — always build fresh.
    rm -rf web/.next
    cd web && npm run build

# full CI locally (lint, type, test, security, a11y, eval gate)
ci: check-cost
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest

# local security suite; pip-audit/osv-scanner/gitleaks/syft/CodeQL run in CI
# (security.yml) — pip-audit's venv bootstrap SIGABRTs on macOS framework Python
security:
    uvx --from semgrep semgrep scan --config p/python --error --exclude data --exclude web/node_modules
    uv run python scripts/check_zero_cost.py

# pa11y (WCAG2AA) against the built static site
a11y:
    @test -d web/out || just build-web
    sh -c 'python3 -m http.server 8031 -d web/out >/dev/null 2>&1 & S=$!; sleep 1; R=0; for r in "" obligations/ authorities/ drafts/ evaluation/ sources/ about/; do npx --yes pa11y@9.1.1 --standard WCAG2AA "http://localhost:8031/$r" || R=$?; done; kill $S; exit $R'

# OSCAL component-definition — de-scoped from this build (docs/PROGRESS.md; the
# governance/ cards + assessment + monitoring/rollback plans ARE present).
govern:
    @echo "de-scoped: OSCAL validation; governance artifacts live in governance/" && exit 1

# scripts/check_zero_cost.py (fails if a non-allowlisted service appears)
check-cost:
    @python3 scripts/check_zero_cost.py
