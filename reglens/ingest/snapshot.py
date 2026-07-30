"""Content-addressed immutable raw snapshots.

Inputs: fetched bytes plus source metadata. Outputs: ``data/raw/<sha256>/``
holding the exact payload and a ``manifest.json``. Failure mode: ``OSError``
propagates on unwritable storage; nothing is partially recorded because the
manifest is written last.

Implements the DETERMINISTIC-REPLAY invariant (CLAUDE.md §2, invariant 5):
snapshots are immutable, addressed by content SHA-256, and re-snapshotting
identical bytes is a no-op.
"""

import hashlib
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

SCHEMA_VERSION = 1


class SnapshotManifest(BaseModel):
    """Provenance record stored beside every raw snapshot."""

    schema_version: int = SCHEMA_VERSION
    source_id: str
    url: str
    fetched_at: str
    sha256: str
    content_type: str
    filename: str


def content_sha256(data: bytes) -> str:
    """Hex SHA-256 of ``data`` — the snapshot's address and identity."""
    return hashlib.sha256(data).hexdigest()


def write_snapshot(
    data_dir: Path,
    *,
    source_id: str,
    url: str,
    content: bytes,
    content_type: str,
    filename: str,
    fetched_at: datetime | None = None,
) -> Path:
    """Persist ``content`` under ``data_dir/raw/<sha256>/`` and return that directory.

    Idempotent: if the manifest already exists for this content hash, the
    existing snapshot is returned untouched (re-running on the same input SHA
    is a no-op).
    """
    sha = content_sha256(content)
    snapshot_dir = data_dir / "raw" / sha
    manifest_path = snapshot_dir / "manifest.json"
    if manifest_path.exists():
        return snapshot_dir

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / filename).write_bytes(content)
    manifest = SnapshotManifest(
        source_id=source_id,
        url=url,
        fetched_at=(fetched_at or datetime.now(UTC)).isoformat(),
        sha256=sha,
        content_type=content_type,
        filename=filename,
    )
    # Manifest written last: its presence marks the snapshot complete.
    manifest_path.write_text(json.dumps(manifest.model_dump(), indent=2) + "\n")
    return snapshot_dir


def read_manifest(snapshot_dir: Path) -> SnapshotManifest:
    """Load and validate the manifest for ``snapshot_dir``.

    Failure mode: raises ``FileNotFoundError`` or pydantic ``ValidationError``;
    a snapshot without a valid manifest is treated as absent, never guessed at.
    """
    return SnapshotManifest.model_validate_json((snapshot_dir / "manifest.json").read_text())


def iter_snapshots(
    raw_root: Path, *, content_type: str | None = None
) -> Iterator[tuple[Path, SnapshotManifest]]:
    """Every complete snapshot under ``raw_root``, in a stable order.

    Yields ``(snapshot_dir, manifest)`` sorted by directory name — the content
    SHA — so downstream "first match wins" logic is reproducible rather than
    dependent on filesystem ordering. Optionally filtered to one ``content_type``.

    Failure mode: a directory without a manifest is skipped, because the manifest
    is written last and its absence means an incomplete snapshot; a missing
    ``raw_root`` yields nothing. Callers that must not proceed on an empty corpus
    are responsible for raising — this iterator reports what exists, it does not
    decide whether that is enough.
    """
    if not raw_root.is_dir():
        return
    for snapshot_dir in sorted(raw_root.iterdir()):
        if not (snapshot_dir / "manifest.json").is_file():
            continue  # incomplete snapshot: ignored, never guessed at
        manifest = read_manifest(snapshot_dir)
        if content_type is None or manifest.content_type == content_type:
            yield snapshot_dir, manifest
