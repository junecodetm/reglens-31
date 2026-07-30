"""Typed runtime configuration.

Inputs: environment variables prefixed ``REGLENS_`` and an optional gitignored
``.env`` file. Outputs: a validated, immutable :class:`Settings` instance.
Failure mode: pydantic raises ``ValidationError`` on malformed values; there is
no silent fallback.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the RegLens pipeline (all local; no secrets required)."""

    model_config = SettingsConfigDict(env_prefix="REGLENS_", env_file=".env", frozen=True)

    data_dir: Path = Path("data")
    ollama_base_url: str = "http://localhost:11434"
    model_tag: str = "qwen3:8b"
    user_agent: str = "reglens-31/0.1 (+https://github.com/junecodetm/reglens-31)"
    ecfr_date: str = "2026-07-01"
    # EXTEND-OGC01 pins: authority-linker snapshots use their own point-in-time
    # date (latest supported by the eCFR versioner at build) so the original
    # claims corpus at ecfr_date stays byte-stable for deterministic replay.
    ecfr_authority_date: str = "2026-07-27"
    # OLRC U.S. Code release point (uscode.house.gov), verified 2026-07-28.
    usc_release_point: str = "119-102"
    max_document_chars: int = 80_000
    extract_workers: int = 8
    """Chunks extracted concurrently against the local runtime.

    Purely a throughput setting: chunk results are reassembled in input order,
    and output was verified bit-identical to a serial run (and run-to-run) at
    temperature 0 with a pinned seed, so the deterministic-replay invariant
    holds. Measured on an M4 with qwen3:8b: 17.8 s/chunk serial vs 8.8 s/chunk
    at 8 workers. Set to 1 to force fully serial extraction.
    """
