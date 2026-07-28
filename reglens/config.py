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
    max_document_chars: int = 80_000
