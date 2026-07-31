# RegLens-31 command surface — docs/COMMANDS.md

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

# close the corpus: every FR final rule amending an in-scope part (reglens/corpus.py)
ingest-corpus:
    uv run python -m reglens.ingest --corpus

# refresh the eCFR section census + amendment dates the currency comparison uses
ecfr-currency:
    uv run python -m reglens.ingest.ecfr_versions

# Which documents are extracted is a rule, not a list
# (reglens.corpus.in_extraction_sample); pass --all for the whole corpus.
# local extraction + provenance gate over the sampled documents, then rebuild stores
extract:
    uv run python -m reglens.extract
    uv run python -m reglens.store.database

# Run this after ANY extraction, including one launched detached, so no stage is
# left stale: the eval harness reads claims, and the exporters read eval plus the
# authority/grounding/draft output. Every stage is idempotent.
# rebuild everything downstream of claims.json, in dependency order, then the site
rebuild: && build-web
    uv run python -m reglens.store.database
    uv run python -m reglens.authority.run
    uv run python -m reglens.grounding.run
    uv run python -m reglens.draft.run
    uv run python -m reglens.memo
    uv run python -m reglens.eval.harness
    uv run python -m reglens.eval.ogc01

# statutory authority: citations -> USLM resolution -> classification
authority:
    uv run python -m reglens.authority.run

# two-sided grounding-marker retrieval (deterministic)
grounding:
    uv run python -m reglens.grounding.run

# DDH skeletons + conformance gates over the full part/doc-type grid
# (narratives from the configured provider; unchanged combinations reused)
draft:
    uv run python -m reglens.draft.run

# per-part review memoranda: deterministic evidence + gated model narrative
memo:
    uv run python -m reglens.memo

# eval harness over the gold set -> metrics + Wilson/bootstrap CIs ($0, offline)
eval:
    uv run python -m reglens.eval.harness
    uv run python -m reglens.eval.ogc01

# eval regression gate (CI): fails on F1 regression or fidelity < 1.0
eval-gate:
    uv run python -m reglens.eval.harness --gate
    uv run python -m reglens.eval.ogc01 --gate

# export site data + the static read API (web/public/api/v1) + Next.js export -> web/out
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

# pip-audit/osv-scanner/gitleaks/syft/CodeQL run in CI (security.yml) —
# pip-audit's venv bootstrap SIGABRTs on macOS framework Python
# local security suite: semgrep, zero-cost allow-list, PII scan
security:
    uvx --from semgrep semgrep scan --config p/python --error --exclude data --exclude web/node_modules
    python3 scripts/check_zero_cost.py
    # docs/ADJUDICATE.md is excluded: it quotes Federal Register text verbatim,
    # including official agency contact blocks (public by law, not PII).
    sh -c 'uv run python scripts/redact_pii.py --check README.md governance/*.md $(ls docs/*.md | grep -v ADJUDICATE)'

# pa11y (WCAG2AA) against the built static site
a11y:
    @test -d web/out || just build-web
    sh -c 'python3 -m http.server 8031 -d web/out >/dev/null 2>&1 & S=$!; sleep 1; R=0; for r in "" obligations/ authorities/ drafts/ evaluation/ sources/; do npx --yes pa11y@9.1.1 --standard WCAG2AA "http://localhost:8031/$r" || R=$?; done; kill $S; exit $R'

# scripts/check_zero_cost.py (fails if a non-allowlisted service appears)
check-cost:
    @python3 scripts/check_zero_cost.py
