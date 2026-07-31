"""The section parser is validated against eCFR's own structure index, not against itself.

``reglens.structure`` derives section spans by parsing flattened part text.
Until this test existed, the only check on that parser was a hand-written count
in tests/test_structure.py — the parser and its expectation had the same author,
so a systematic parsing error would have satisfied both.

These tests compare it instead to the census eCFR publishes at
``/api/versioner/v1/structure/{date}/title-31.json?part=N``, snapshotted
content-addressed by :mod:`reglens.ingest.ecfr_versions`. They run entirely
offline against those committed snapshots.
"""

import json
from pathlib import Path

import pytest

from reglens.corpus import CFR_PARTS, part_document_number
from reglens.currency import CurrencyExport, build_currency_export
from reglens.ingest.ecfr_versions import SOURCE_INDEX_PATH
from reglens.structure import split_part_text

DATA_DIR = Path(__file__).parents[1] / "data"
PART_TEXT_DIR = Path(__file__).parents[1] / "web" / "public" / "data" / "authority-parts"


@pytest.fixture(scope="module")
def currency() -> CurrencyExport:
    """The currency baseline built from the committed eCFR snapshots."""
    if not (DATA_DIR / SOURCE_INDEX_PATH).is_file():
        pytest.fail(
            "data/reference/ecfr-currency-sources.json is missing — "
            "run `just ecfr-currency` to refresh the committed snapshots"
        )
    return build_currency_export(DATA_DIR)


def test_every_in_scope_part_has_a_committed_census(currency: CurrencyExport) -> None:
    assert [part.part for part in currency.parts] == list(CFR_PARTS)


@pytest.mark.parametrize("part", CFR_PARTS)
def test_parsed_section_count_matches_the_official_ecfr_census(
    currency: CurrencyExport, part: int
) -> None:
    """The external check: our parser must find exactly the sections eCFR lists."""
    census = next(entry for entry in currency.parts if entry.part == part)
    text = (PART_TEXT_DIR / f"{part_document_number(part)}.txt").read_text()

    parsed = split_part_text(
        part=part,
        heading=f"Part {part}",
        text_path=f"authority-parts/{part_document_number(part)}.txt",
        text=text,
    )

    assert len(parsed.sections) == census.census_count


def test_the_baseline_records_the_pinned_snapshot_date(currency: CurrencyExport) -> None:
    """Drift is measured against the corpus's pinned date, not against 'now'."""
    from reglens.config import Settings

    assert currency.snapshot_date == Settings().ecfr_date


def test_amended_counts_are_consistent_with_the_per_section_flags(currency: CurrencyExport) -> None:
    for part in currency.parts:
        assert part.amended_since_snapshot == sum(
            1 for section in part.sections if section.amended_since_snapshot
        )
        assert all(
            section.amended_since_snapshot
            == (section.latest_amendment_date > currency.snapshot_date)
            for section in part.sections
        )
    assert currency.total_amended_since_snapshot == sum(
        part.amended_since_snapshot for part in currency.parts
    )


def test_the_published_census_and_drift_are_pinned(currency: CurrencyExport) -> None:
    """The site publishes these numbers, so a snapshot refresh must be a deliberate edit.

    Sourced from eCFR's own structure and versions endpoints, not hand-counted;
    tests/test_structure.py pins the same section counts for the parser.
    """
    expected = {50: (62, 0), 223: (21, 0), 285: (11, 0), 356: (26, 0), 501: (65, 3)}

    assert {
        part.part: (part.census_count, part.amended_since_snapshot) for part in currency.parts
    } == expected
    assert currency.total_sections == sum(census for census, _ in expected.values())
    assert currency.total_amended_since_snapshot == sum(amended for _, amended in expected.values())


def test_the_exported_currency_artifact_round_trips(currency: CurrencyExport) -> None:
    """What the site reads is this object, not a hand-shaped copy of it."""
    exported = Path(__file__).parents[1] / "web" / "public" / "data" / "currency.json"
    if not exported.is_file():
        pytest.fail("web/public/data/currency.json is missing — run `just build-web`")

    assert CurrencyExport.model_validate_json(exported.read_text()) == currency


def test_source_index_digests_match_the_committed_snapshots(currency: CurrencyExport) -> None:
    """build_currency_export re-verifies every payload; this pins that it covers all of them."""
    index = json.loads((DATA_DIR / SOURCE_INDEX_PATH).read_text())

    assert len(index["sources"]) == 2 * len(CFR_PARTS)
    assert {source["kind"] for source in index["sources"]} == {"versions", "structure"}
    assert [source.sha256 for source in currency.sources] == [
        source["sha256"] for source in index["sources"]
    ]
