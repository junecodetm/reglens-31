# Coding Standards

> Decomposed from CLAUDE.md §5 (2026-07-28). A condensed version lives in the CLAUDE.md core; this is the full text.

- Python 3.13, full type hints, `pyright` strict on `reglens/`. `ruff` for lint + format; no unformatted code merges.
- Pydantic v2 models for every external payload and every extracted record; no untyped dicts crossing module boundaries.
- Pure functions where possible; side effects (network, disk) isolated in `ingest/` and `store/`.
- Determinism: LLM calls use temperature 0 and a pinned model tag; every run records model id, prompt hash, and input SHA.
- No secret in code; config via env + `.env` (gitignored); `pydantic-settings` for typed config.
- Docstrings state inputs, outputs, and failure mode. Every fail-closed path is commented as such.
- Tests: `pytest` + `respx`/`vcrpy` cassettes for HTTP + `hypothesis` for the provenance normalizer.
