"""Typed runtime configuration.

Inputs: environment variables prefixed ``REGLENS_`` and an optional gitignored
``.env`` file. Outputs: a validated, immutable :class:`Settings` instance.
Failure mode: pydantic raises ``ValidationError`` on malformed values; there is
no silent fallback.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the RegLens pipeline.

    The extraction pipeline is local-only and needs no secrets. The draft
    stage may use the hosted Groq free tier (``draft_provider="groq"``), in
    which case ``groq_api_key`` must be set via the environment or the
    gitignored ``.env`` — never in code or committed configuration.
    """

    model_config = SettingsConfigDict(env_prefix="REGLENS_", env_file=".env", frozen=True)

    data_dir: Path = Path("data")
    ollama_base_url: str = "http://localhost:11434"
    model_tag: str = "qwen3:8b"
    user_agent: str = "reglens-31/0.1 (+https://github.com/junecodetm/reglens-31)"
    ecfr_date: str = "2026-07-01"
    # Authority-linker snapshots use their own point-in-time date (latest
    # supported by the eCFR versioner at build) so the original claims corpus
    # at ecfr_date stays byte-stable for deterministic replay.
    ecfr_authority_date: str = "2026-07-27"
    # OLRC U.S. Code release point (uscode.house.gov), verified 2026-07-28.
    usc_release_point: str = "119-102"
    max_document_chars: int = 80_000
    # Draft-narrative provider (docs/STACK.md adapter pattern). "local" is the
    # default so a fresh clone runs fully offline; "groq" pins the hosted
    # free-tier model recorded in every draft dossier. Extraction NEVER uses
    # the hosted provider — it is local-only by design.
    draft_provider: Literal["local", "groq"] = "local"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model_tag: str = "openai/gpt-oss-120b"
    groq_api_key: str | None = None
    extract_workers: int = 2
    """Chunks extracted concurrently against the local runtime.

    This is a throughput setting; chunk results are reassembled in input order.
    On the 16 GB reference machine, one, two, and four workers have comparable
    throughput, while eight workers create memory pressure. The default of two
    avoids that pressure. Set the value to one for serial extraction.
    """
