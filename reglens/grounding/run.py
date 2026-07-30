"""Stage 2 pipeline: marker retrieval over FR documents → grounding.json.

Inputs: the FR document snapshots already in ``data/raw`` (the 20-rule
corpus plus the four per-part source preambles). Outputs:
``data/processed/grounding.json``. Failure mode: a part whose source
preamble is not retrievable is recorded as a first-class coverage fact
("preamble unavailable"), fail-closed — never synthesized.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from reglens.config import Settings
from reglens.extract.run import discover_documents
from reglens.grounding.markers import (
    GROUNDING_SCHEMA_VERSION,
    LOPER_BRIGHT_DECIDED,
    MarkerSpan,
    density_band,
    scan_markers,
)

GROUNDING_JSON = Path("data/processed/grounding.json")

# CFR part → the FR document that is the part's "Source" preamble, resolved
# from each part's eCFR SOURCE line via the FR API date + page-range lookup
# (reglens.ingest.federal_register.find_rule_by_citation), then snapshotted:
#   part 501 ← 62 FR 45101 (1997-08-25) → 97-22378
#   part 50  ← 81 FR 93765 (2016-12-21) → 2016-29987
#   part 356 ← 69 FR 45202 (2004-07-28) → 04-17012
#   part 285 ← 62 FR 34179 (1997-06-25) → 97-16181
# Part 223 has NO Source line in the eCFR (its basis predates FR API
# coverage): recorded below as "preamble unavailable" — a coverage fact.
PART_SOURCE_DOCS: dict[int, str | None] = {
    50: "2016-29987",
    223: None,
    285: "97-16181",
    356: "04-17012",
    501: "97-22378",
}


class RuleGrounding(BaseModel):
    """Marker retrieval result + neutral facts for one FR document."""

    document_number: str
    title: str
    publication_date: str | None
    source_for_part: int | None = None
    # Facts (EXTEND-OGC01 Stage 2.4) — recorded, not judged:
    predates_loper_bright: bool | None
    cites_chevron: bool
    word_count: int
    deference_count: int
    grounding_count: int
    deference_density_per_1k: float
    grounding_density_per_1k: float
    deference_band: str
    grounding_band: str
    gate_rejections: int
    markers: list[MarkerSpan]


class GroundingExport(BaseModel):
    """Top-level payload for ``grounding.json``."""

    schema_version: int = GROUNDING_SCHEMA_VERSION
    band_definition: str = (
        "Bands report TEXTUAL-MARKER DENSITY only (listed phrase families per "
        "1,000 words; none=0, low≤0.2, moderate≤0.6, elevated>0.6), applied "
        "identically to both marker families. They describe phrase frequency in "
        "the published document text and are not a prediction of any judicial "
        "outcome or a statement about any regulation's validity."
    )
    loper_bright_decided: str = LOPER_BRIGHT_DECIDED
    rules: list[RuleGrounding]
    coverage_notes: list[str] = Field(default_factory=list[str])
    total_gate_rejections: int


def _publication_dates(settings: Settings) -> dict[str, str]:
    """document number → publication_date from the FR metadata snapshots."""
    import json

    from reglens.ingest.snapshot import iter_snapshots

    dates: dict[str, str] = {}
    raw_root = settings.data_dir / "raw"
    if not raw_root.is_dir():
        return dates
    for snapshot_dir, manifest in iter_snapshots(raw_root, content_type="application/json"):
        payload = json.loads((snapshot_dir / manifest.filename).read_bytes())
        number = payload.get("document_number")
        date = payload.get("publication_date")
        if isinstance(number, str) and isinstance(date, str):
            dates[number] = date
    return dates


def build_grounding(settings: Settings) -> GroundingExport:
    """Scan every FR document snapshot (the eCFR part snapshots are skipped)."""
    source_doc_to_part = {doc: part for part, doc in PART_SOURCE_DOCS.items() if doc}
    rules: list[RuleGrounding] = []
    total_rejections = 0
    publication_dates = _publication_dates(settings)
    metadata_by_number = {
        pair.document_number: pair for pair in discover_documents(settings.data_dir)
    }
    for document_number, pair in sorted(metadata_by_number.items()):
        if document_number.startswith("31-CFR-"):
            continue  # eCFR part text is not an FR document; no preamble to scan
        scan = scan_markers(pair.text)
        total_rejections += scan.gate_rejections
        publication_date = publication_dates.get(document_number)
        deference = [m for m in scan.markers if m.side == "deference-reliance"]
        grounding = [m for m in scan.markers if m.side == "grounding-strength"]
        deference_density, deference_bd = density_band(len(deference), scan.word_count)
        grounding_density, grounding_bd = density_band(len(grounding), scan.word_count)
        rules.append(
            RuleGrounding(
                document_number=document_number,
                title=pair.title,
                publication_date=publication_date,
                source_for_part=source_doc_to_part.get(document_number),
                predates_loper_bright=(
                    publication_date < LOPER_BRIGHT_DECIDED if publication_date else None
                ),
                cites_chevron=any(m.family == "chevron-citation" for m in scan.markers),
                word_count=scan.word_count,
                deference_count=len(deference),
                grounding_count=len(grounding),
                deference_density_per_1k=round(deference_density, 4),
                grounding_density_per_1k=round(grounding_density, 4),
                deference_band=deference_bd,
                grounding_band=grounding_bd,
                gate_rejections=scan.gate_rejections,
                markers=scan.markers,
            )
        )
    coverage = [
        f"31 CFR part {part}: source preamble unavailable (no eCFR Source line; "
        "predates Federal Register API coverage). Recorded as a coverage fact, "
        "not synthesized."
        for part, doc in sorted(PART_SOURCE_DOCS.items())
        if doc is None
    ]
    return GroundingExport(
        rules=rules,
        coverage_notes=coverage,
        total_gate_rejections=total_rejections,
    )


def main() -> int:
    settings = Settings()
    export = build_grounding(settings)
    GROUNDING_JSON.parent.mkdir(parents=True, exist_ok=True)
    GROUNDING_JSON.write_text(export.model_dump_json(indent=2) + "\n")
    print(
        f"grounding: {len(export.rules)} documents scanned, "
        f"{sum(r.deference_count for r in export.rules)} deference-reliance / "
        f"{sum(r.grounding_count for r in export.rules)} grounding-strength markers, "
        f"{export.total_gate_rejections} gate rejections"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
