"""SQLite system of record + DuckDB/Parquet analytics export.

Inputs: ``data/processed/claims.json``. Outputs: ``data/processed/reglens.db``
(SQLite, one row per claim), ``data/processed/claims.parquet``, and an
obligation-type summary. Failure mode: a missing claims file raises; both
stores are rebuilt atomically from scratch each run (deterministic, idempotent
for identical input).
"""

import sqlite3
from pathlib import Path
from typing import Any

import duckdb

from reglens.extract.records import load_extractions

CLAIM_COLUMNS = (
    "claim_id",
    "document_sha256",
    "document_number",
    "document_title",
    "document_url",
    "quote",
    "obligation_type",
    "affected_party",
    "summary",
    "effective_date",
    "accepted",
    "start",
    "end",
    "rejection_reason",
)


def _claim_rows(claims_path: Path) -> list[tuple[Any, ...]]:
    return [
        tuple(claim.model_dump()[column] for column in CLAIM_COLUMNS)
        for extraction in load_extractions(claims_path)
        for claim in extraction.claims
    ]


def write_sqlite(claims_path: Path, db_path: Path) -> int:
    """Rebuild the claims table from scratch; returns the row count."""
    rows = _claim_rows(claims_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("DROP TABLE IF EXISTS claims")
        connection.execute(
            """
            CREATE TABLE claims (
                claim_id TEXT PRIMARY KEY, document_sha256 TEXT NOT NULL,
                document_number TEXT NOT NULL, document_title TEXT NOT NULL,
                document_url TEXT NOT NULL, quote TEXT NOT NULL,
                obligation_type TEXT NOT NULL, affected_party TEXT NOT NULL,
                summary TEXT NOT NULL, effective_date TEXT,
                accepted INTEGER NOT NULL, start INTEGER, "end" INTEGER,
                rejection_reason TEXT
            )
            """
        )
        connection.executemany(
            f"INSERT INTO claims VALUES ({', '.join('?' * len(CLAIM_COLUMNS))})", rows
        )
    return len(rows)


def export_parquet(db_path: Path, parquet_path: Path) -> list[tuple[str, str, int]]:
    """Write claims to Parquet via DuckDB; return (document, type, n) accepted-claim stats."""
    # ATTACH/COPY do not take bound parameters; single quotes in paths are escaped.
    db_literal = str(db_path).replace("'", "''")
    parquet_literal = str(parquet_path).replace("'", "''")
    with duckdb.connect() as connection:
        connection.execute(f"ATTACH '{db_literal}' AS records (TYPE sqlite)")
        connection.execute(
            "COPY (SELECT * FROM records.claims ORDER BY claim_id) "
            f"TO '{parquet_literal}' (FORMAT parquet)"
        )
        result = connection.execute(
            """
            SELECT document_number, obligation_type, count(*) AS n
            FROM records.claims WHERE accepted
            GROUP BY document_number, obligation_type
            ORDER BY document_number, obligation_type
            """
        ).fetchall()
    return [
        (str(document), str(obligation_type), int(count))
        for document, obligation_type, count in result
    ]


def main() -> int:
    from reglens.config import Settings

    processed = Settings().data_dir / "processed"
    count = write_sqlite(processed / "claims.json", processed / "reglens.db")
    stats = export_parquet(processed / "reglens.db", processed / "claims.parquet")
    print(f"{count} claims -> reglens.db + claims.parquet ({len(stats)} doc/type groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
