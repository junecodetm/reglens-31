"""Typed parse of the Treasury AI Use Case Inventory reference snapshot.

Inputs: the exact bytes of the snapshotted inventory CSV (see
``reglens.ingest.inventory``). Outputs: the verbatim OGC-01 row in CSV column
order plus deterministic corpus context (row count, high-impact entries,
General Counsel entries) that backs the site's "About this demonstration"
claims. Failure mode: ``ValueError`` when the expected structure or the
OGC-01 row is absent — fail-closed, never a guessed or partial record.
"""

import csv
import io

from pydantic import BaseModel, Field

OGC01_USE_CASE_ID = "OGC-01"
# Row 0 is a merged section band ("SECTION 1: ..."); row 1 holds column names.
_HEADER_ROW_INDEX = 1
_ID_HEADER = "Use Case ID"
_NAME_HEADER = "Use Case Name"
_BUREAU_HEADER = "Bureau/Component"
_HIGH_IMPACT_HEADER = "Is the AI use case high-impact?"
_HIGH_IMPACT_VALUE = "High-impact"


class HighImpactUseCase(BaseModel):
    """One inventory row flagged high-impact (whitespace-trimmed labels)."""

    use_case_id: str
    name: str
    bureau: str


class InventoryContext(BaseModel):
    """Deterministic corpus facts computed from the full inventory."""

    total_use_cases: int = Field(ge=0)
    high_impact: list[HighImpactUseCase]
    general_counsel_use_case_ids: list[str]


class UseCaseInventoryData(BaseModel):
    """The verbatim OGC-01 row (CSV column order) plus corpus context."""

    row: dict[str, str]
    context: InventoryContext


class UseCaseInventoryExport(BaseModel):
    """The published reference record: snapshot provenance + parsed data."""

    schema_version: int = 1
    source_url: str
    fetched_at: str
    sha256: str
    row: dict[str, str]
    context: InventoryContext


def parse_inventory_csv(content: bytes) -> UseCaseInventoryData:
    """Extract the verbatim OGC-01 row and corpus context from the CSV bytes.

    Args:
        content: Exact snapshot bytes (UTF-8, optional BOM).

    Returns:
        ``UseCaseInventoryData`` whose ``row`` maps each verbatim column
        header to the OGC-01 row's verbatim value, in CSV column order.

    Raises:
        ValueError: If the header row, a required column, or exactly one
            OGC-01 row cannot be found, or any data row is ragged —
            fail-closed against silent structural drift in the source file.
    """
    rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))
    if len(rows) <= _HEADER_ROW_INDEX + 1:
        raise ValueError("inventory CSV is shorter than its header plus one data row")
    headers = rows[_HEADER_ROW_INDEX]
    if len(set(headers)) != len(headers):
        raise ValueError("inventory CSV header names are not unique")
    try:
        id_column = headers.index(_ID_HEADER)
        name_column = headers.index(_NAME_HEADER)
        bureau_column = headers.index(_BUREAU_HEADER)
        high_impact_column = headers.index(_HIGH_IMPACT_HEADER)
    except ValueError as error:
        raise ValueError("inventory CSV is missing a required column header") from error

    data_rows = rows[_HEADER_ROW_INDEX + 1 :]
    ragged = [index for index, row in enumerate(data_rows) if len(row) != len(headers)]
    if ragged:
        raise ValueError(f"inventory CSV data rows have unexpected widths at {ragged}")

    ogc_rows = [row for row in data_rows if row[id_column].strip() == OGC01_USE_CASE_ID]
    if len(ogc_rows) != 1:
        raise ValueError(f"expected exactly one {OGC01_USE_CASE_ID} row, found {len(ogc_rows)}")

    context = InventoryContext(
        total_use_cases=len(data_rows),
        high_impact=[
            HighImpactUseCase(
                use_case_id=row[id_column].strip(),
                name=row[name_column].strip(),
                bureau=row[bureau_column].strip(),
            )
            for row in data_rows
            if row[high_impact_column].strip() == _HIGH_IMPACT_VALUE
        ],
        general_counsel_use_case_ids=[
            row[id_column].strip()
            for row in data_rows
            if row[bureau_column].strip() == "General Counsel"
        ],
    )
    return UseCaseInventoryData(row=dict(zip(headers, ogc_rows[0], strict=True)), context=context)
