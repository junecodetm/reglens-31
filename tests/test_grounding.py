"""Two-sided marker retrieval: families, densities, facts, and coverage notes."""

import json
from pathlib import Path

from reglens.config import Settings
from reglens.grounding.markers import density_band, scan_markers
from reglens.grounding.run import build_grounding
from reglens.ingest.snapshot import write_snapshot

SAMPLE = (
    "Under Chevron, the agency read the statute as silent or ambiguous and "
    "adopted a permissible construction. Separately, section 9 directs the "
    "Secretary to issue standards, as required by the Act."
)


def test_scan_finds_both_sides_with_exact_spans() -> None:
    scan = scan_markers(SAMPLE)
    families = {m.family for m in scan.markers}
    assert {"chevron-citation", "silent-or-ambiguous", "permissible-construction"} <= families
    assert {"directs-the-secretary", "as-required-by"} <= families
    sides = {m.side for m in scan.markers}
    assert sides == {"deference-reliance", "grounding-strength"}
    for marker in scan.markers:
        assert SAMPLE[marker.start : marker.end] == marker.quote
    assert scan.gate_rejections == 0


def test_chevron_is_case_sensitive() -> None:
    scan = scan_markers("a chevron pattern on the sleeve")
    assert not any(m.family == "chevron-citation" for m in scan.markers)


def test_density_bands_are_definitional() -> None:
    assert density_band(0, 1000) == (0.0, "none")
    assert density_band(1, 10_000)[1] == "low"  # 0.1/1k
    assert density_band(5, 10_000)[1] == "moderate"  # 0.5/1k
    assert density_band(10, 10_000)[1] == "elevated"  # 1.0/1k
    assert density_band(3, 0) == (0.0, "none")


def test_build_grounding_facts_and_coverage(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")

    def snap(number: str, date: str | None, text: str) -> None:
        metadata: dict[str, str] = {"document_number": number, "title": number, "html_url": ""}
        if date:
            metadata["publication_date"] = date
        write_snapshot(
            settings.data_dir,
            source_id="federal_register",
            url=f"https://www.federalregister.gov/api/v1/documents/{number}.json",
            content=json.dumps(metadata).encode(),
            content_type="application/json",
            filename=f"{number}.json",
        )
        write_snapshot(
            settings.data_dir,
            source_id="federal_register",
            url=f"https://www.federalregister.gov/documents/full_text/text/{number}.txt",
            content=text.encode(),
            content_type="text/plain",
            filename=f"{number}.txt",
        )

    snap("97-00001", "1997-08-25", "The statute was silent or ambiguous; see Chevron.")
    snap("2026-00002", "2026-01-05", "Section 12 directs the Secretary to act.")
    snap("31-CFR-999", None, "Part text that must be skipped, Chevron or not.")

    export = build_grounding(settings)
    numbers = [rule.document_number for rule in export.rules]
    assert numbers == ["2026-00002", "97-00001"]  # eCFR part skipped

    old = next(r for r in export.rules if r.document_number == "97-00001")
    assert old.predates_loper_bright is True
    assert old.cites_chevron is True
    assert old.deference_count == 2 and old.grounding_count == 0

    new = next(r for r in export.rules if r.document_number == "2026-00002")
    assert new.predates_loper_bright is False
    assert new.cites_chevron is False
    assert new.grounding_count == 1

    assert any("part 223" in note for note in export.coverage_notes)
    assert export.total_gate_rejections == 0
    assert "not a prediction" in export.band_definition
