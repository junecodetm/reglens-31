"""Content-addressed snapshots: deterministic addressing, complete manifests, idempotent re-runs."""

from datetime import UTC, datetime
from pathlib import Path

from reglens.ingest.snapshot import content_sha256, read_manifest, write_snapshot


def _write(tmp_path: Path, content: bytes) -> Path:
    return write_snapshot(
        tmp_path,
        source_id="federal_register",
        url="https://www.federalregister.gov/api/v1/documents/X.json",
        content=content,
        content_type="application/json",
        filename="X.json",
        fetched_at=datetime(2026, 7, 28, tzinfo=UTC),
    )


def test_snapshot_is_content_addressed(tmp_path: Path) -> None:
    content = b'{"a": 1}'
    snapshot_dir = _write(tmp_path, content)
    assert snapshot_dir.name == content_sha256(content)
    assert (snapshot_dir / "X.json").read_bytes() == content
    manifest = read_manifest(snapshot_dir)
    assert manifest.sha256 == content_sha256(content)
    assert manifest.source_id == "federal_register"


def test_rerun_on_same_input_is_a_noop(tmp_path: Path) -> None:
    content = b"same bytes"
    first = _write(tmp_path, content)
    marker = first / "X.json"
    original_mtime = marker.stat().st_mtime_ns
    second = _write(tmp_path, content)
    assert second == first
    assert marker.stat().st_mtime_ns == original_mtime


def test_different_content_gets_a_different_address(tmp_path: Path) -> None:
    a = _write(tmp_path, b"one")
    b = _write(tmp_path, b"two")
    assert a != b
