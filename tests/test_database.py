"""SQLite + Parquet store round-trip on a small claims fixture."""

import json
import sqlite3
from pathlib import Path

from reglens.extract.records import ClaimRecord, DocumentExtraction
from reglens.extract.schema import RunMeta
from reglens.store.database import export_parquet, write_sqlite

RUN = RunMeta(model_tag="fake", prompt_sha256="0" * 64, input_sha256="1" * 64)


def make_claim(claim_id: str, accepted: bool) -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        document_sha256="d" * 64,
        document_number="2026-00001",
        document_title="Test Rule",
        document_url="https://www.federalregister.gov/documents/2026-00001",
        quote="Each bank must report.",
        obligation_type="reporting",
        affected_party="banks",
        summary="Report.",
        effective_date=None,
        accepted=accepted,
        start=0 if accepted else None,
        end=22 if accepted else None,
        rejection_reason=None if accepted else "not-a-substring",
        run=RUN,
    )


def _claims_fixture(tmp_path: Path) -> Path:
    extraction = DocumentExtraction(
        document_sha256="d" * 64,
        document_number="2026-00001",
        document_title="Test Rule",
        document_url="https://www.federalregister.gov/documents/2026-00001",
        accepted_count=1,
        rejected_count=1,
        total_chars=100,
        extracted_chars=100,
        claims=[make_claim("abc123", True), make_claim("def456", False)],
    )
    path = tmp_path / "claims.json"
    path.write_text(json.dumps([extraction.model_dump()]))
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
