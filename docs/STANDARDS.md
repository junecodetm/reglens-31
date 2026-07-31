# Coding standards

- Production Python targets version 3.13 and uses complete type annotations.
  `pyright` runs in strict mode over `reglens/`; `ruff` provides linting and
  formatting.
- Pydantic v2 models validate every external payload and extracted record.
  Untyped dictionaries do not cross module boundaries.
- Pure functions are preferred. Network side effects are isolated in
  `reglens/ingest/` and `reglens/extract/llm.py`; artifact writes are isolated
  in `reglens/store/` and thin command-line entry points.
- Model calls use temperature 0 and a pinned model tag. Each run records the
  model identifier, prompt hash, and input SHA.
- Source code contains no secrets. Environment variables and a gitignored
  `.env` file provide configuration through `pydantic-settings`.
- Docstrings state inputs, outputs, and failure modes. Comments identify
  fail-closed paths.
- Tests use `pytest`, `respx` or `vcrpy` cassettes for HTTP behavior, and
  `hypothesis` for provenance normalization.
