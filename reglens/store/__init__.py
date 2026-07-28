"""Storage and export: persistence helpers for pipeline artifacts.

Side-effect policy (docs/STANDARDS.md): network I/O lives in ingest/ and in
extract/llm.py (the local model call); artifact writes live here and in the
thin CLI entry points that persist their module's own outputs.
"""
