"""Content-addressed snapshots: deterministic addressing, complete manifests, idempotent re-runs."""

from datetime import UTC, datetime
from pathlib import Path

from reglens.ingest.snapshot import (
    content_sha256,
    iter_snapshots,
    read_manifest,
    write_snapshot,
)


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


def _write_typed(tmp_path: Path, content: bytes, content_type: str, filename: str) -> Path:
    return write_snapshot(
        tmp_path,
        source_id="federal_register",
        url=f"https://www.federalregister.gov/{filename}",
        content=content,
        content_type=content_type,
        filename=filename,
        fetched_at=datetime(2026, 7, 28, tzinfo=UTC),
    )


def test_iter_snapshots_is_ordered_by_content_address(tmp_path: Path) -> None:
    """Stable order matters: several callers take the FIRST match, so it must not
    depend on filesystem enumeration order."""
    for index in range(6):
        _write_typed(tmp_path, f'{{"n": {index}}}'.encode(), "application/json", "d.json")

    found = [snapshot_dir.name for snapshot_dir, _ in iter_snapshots(tmp_path / "raw")]

    assert found == sorted(found)
    assert len(found) == 6


def test_iter_snapshots_filters_by_content_type(tmp_path: Path) -> None:
    _write_typed(tmp_path, b'{"a": 1}', "application/json", "meta.json")
    _write_typed(tmp_path, b"Each person must file.", "text/plain", "body.txt")

    text_only = [
        manifest.filename
        for _, manifest in iter_snapshots(tmp_path / "raw", content_type="text/plain")
    ]

    assert text_only == ["body.txt"]


def test_iter_snapshots_skips_incomplete_snapshots(tmp_path: Path) -> None:
    """The manifest is written last, so a directory without one is a partial write."""
    complete = _write_typed(tmp_path, b'{"a": 1}', "application/json", "meta.json")
    partial = tmp_path / "raw" / ("0" * 64)
    partial.mkdir(parents=True)
    (partial / "meta.json").write_bytes(b'{"a": 2}')

    found = [snapshot_dir for snapshot_dir, _ in iter_snapshots(tmp_path / "raw")]

    assert found == [complete]


def test_iter_snapshots_on_a_missing_root_yields_nothing(tmp_path: Path) -> None:
    assert list(iter_snapshots(tmp_path / "raw")) == []
