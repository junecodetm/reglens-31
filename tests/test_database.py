"""SQLite + Parquet store round-trip on a small claims fixture."""

import json
import sqlite3
from pathlib import Path

from reglens.store.database import export_parquet, write_sqlite


def _claims_fixture(tmp_path: Path) -> Path:
    claim = {
        "claim_id": "abc123",
        "document_sha256": "d" * 64,
        "document_number": "2026-00001",
        "document_title": "Test Rule",
        "document_url": "https://www.federalregister.gov/documents/2026-00001",
        "quote": "Each bank must report.",
        "obligation_type": "reporting",
        "affected_party": "banks",
        "summary": "Report.",
        "effective_date": None,
        "accepted": True,
        "start": 0,
        "end": 22,
        "rejection_reason": None,
    }
    rejected = {**claim, "claim_id": "def456", "accepted": False, "start": None, "end": None}
    path = tmp_path / "claims.json"
    path.write_text(json.dumps([{"document_number": "2026-00001", "claims": [claim, rejected]}]))
    return path


def test_sqlite_and_parquet_roundtrip(tmp_path: Path) -> None:
    claims_path = _claims_fixture(tmp_path)
    db_path = tmp_path / "reglens.db"
    assert write_sqlite(claims_path, db_path) == 2

    with sqlite3.connect(db_path) as connection:
        accepted = connection.execute("SELECT count(*) FROM claims WHERE accepted").fetchone()[0]
    assert accepted == 1

    parquet_path = tmp_path / "claims.parquet"
    stats = export_parquet(db_path, parquet_path)
    assert parquet_path.is_file()
    assert stats == [("2026-00001", "reporting", 1)]
