"""Currency of the pinned corpus: what has been amended since the snapshot date.

Inputs: the snapshotted eCFR ``versions`` and ``structure`` responses recorded
by :mod:`reglens.ingest.ecfr_versions`. Outputs: a typed baseline naming, per
in-scope part, the authoritative section census and each section's latest
recorded amendment date, plus how many of those postdate ``Settings.ecfr_date``.

Failure mode: a malformed payload, or a census section with no amendment
record, raises — a currency claim is never published from data that does not
hold together (fail-closed). Never touches the network.

This makes the staleness trigger in ``governance/monitoring_plan.md`` an
executable check rather than a written policy, and it supplies the census that
``reglens.structure``'s section parser is validated against.
"""

from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel, Field

from reglens.corpus import CFR_PARTS
from reglens.ingest.ecfr_versions import (
    CurrencySource,
    StructureNode,
    VersionsResponse,
    load_source_index,
    parse_structure,
    parse_versions,
    read_source_bytes,
)


class SectionCurrency(BaseModel):
    """One section's latest recorded amendment, as the eCFR versioner reports it."""

    identifier: str
    latest_amendment_date: str
    amended_since_snapshot: bool


class PartCurrency(BaseModel):
    """One in-scope CFR part: its official census and its sections' amendment dates."""

    part: int
    census_count: int = Field(ge=0)
    sections: list[SectionCurrency]
    amended_since_snapshot: int = Field(ge=0)


class CurrencyExport(BaseModel):
    """The published currency baseline, including the provenance it was built from."""

    schema_version: int = 1
    snapshot_date: str
    sources: list[CurrencySource]
    parts: list[PartCurrency]
    total_sections: int = Field(ge=0)
    total_amended_since_snapshot: int = Field(ge=0)


def _iter_nodes(node: StructureNode) -> Iterator[StructureNode]:
    """Every node of a structure tree, depth-first in document order."""
    yield node
    for child in node.children or ():
        yield from _iter_nodes(child)


def census_identifiers(structure: StructureNode) -> list[str]:
    """Section identifiers the eCFR structure index lists, in document order.

    This is the authoritative census: what eCFR itself says the part contains,
    independent of any parsing this project does.
    """
    return [
        node.identifier
        for node in _iter_nodes(structure)
        if node.type == "section" and node.identifier
    ]


def latest_amendments(versions: VersionsResponse) -> dict[str, str]:
    """The latest ``amendment_date`` recorded per section identifier.

    Removal records count: a removed section's last amendment is still the last
    thing that happened to it, and excluding those would understate drift.
    """
    latest: dict[str, str] = {}
    for record in versions.content_versions:
        if record.type != "section" or not record.identifier or not record.amendment_date:
            continue
        if record.amendment_date > latest.get(record.identifier, ""):
            latest[record.identifier] = record.amendment_date
    return latest


def build_part_currency(
    part: int, structure: StructureNode, versions: VersionsResponse, snapshot_date: str
) -> PartCurrency:
    """Join one part's census to its amendment history.

    Failure mode: a census section with no version record raises — a section
    whose currency cannot be established is never reported as current.
    """
    identifiers = census_identifiers(structure)
    latest = latest_amendments(versions)
    missing = [identifier for identifier in identifiers if identifier not in latest]
    if missing:
        raise ValueError(f"31 CFR part {part}: no amendment record for sections {missing}")
    sections = [
        SectionCurrency(
            identifier=identifier,
            latest_amendment_date=latest[identifier],
            amended_since_snapshot=latest[identifier] > snapshot_date,
        )
        for identifier in identifiers
    ]
    return PartCurrency(
        part=part,
        census_count=len(identifiers),
        sections=sections,
        amended_since_snapshot=sum(1 for section in sections if section.amended_since_snapshot),
    )


def build_currency_export(data_dir: Path) -> CurrencyExport:
    """Assemble the currency baseline from the committed snapshots only.

    Failure mode: a missing snapshot, a digest mismatch, or a part named in
    :data:`reglens.corpus.CFR_PARTS` lacking either of its two sources raises.
    """
    index = load_source_index(data_dir)
    structures: dict[int, StructureNode] = {}
    versions: dict[int, VersionsResponse] = {}
    for source in index.sources:
        content = read_source_bytes(data_dir, source)
        if source.kind == "structure":
            structures[source.part] = parse_structure(content)
        else:
            versions[source.part] = parse_versions(content)

    parts: list[PartCurrency] = []
    for part in CFR_PARTS:
        if part not in structures or part not in versions:
            raise ValueError(f"currency sources incomplete for 31 CFR part {part}")
        parts.append(
            build_part_currency(part, structures[part], versions[part], index.snapshot_date)
        )
    return CurrencyExport(
        snapshot_date=index.snapshot_date,
        sources=index.sources,
        parts=parts,
        total_sections=sum(part.census_count for part in parts),
        total_amended_since_snapshot=sum(part.amended_since_snapshot for part in parts),
    )
