"""Pinned OLRC U.S. Code ingest stays offline and excludes non-statutory text."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from reglens.config import Settings
from reglens.ingest.snapshot import read_manifest
from reglens.ingest.uscode import (
    extract_sections,
    fetch_title_zip,
    snapshot_sections,
    title_zip_url,
)

USLM_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<uscDoc xmlns="http://xml.house.gov/schemas/uslm/1.0">
  <section identifier="/us/usc/t99/s101">
    <heading>Required records</heading>
    <subsection>
      <num>(a)</num>
      <content>Subsection body text must remain quotable.</content>
    </subsection>
    <sourceCredit>Source credit must not be quoted.</sourceCredit>
    <notes>
      <note>Editorial note must not be quoted.</note>
    </notes>
  </section>
  <section identifier="/us/usc/t99/s102" status="repealed">
    <heading>Repealed provision</heading>
    <content>Minimal repealed text.</content>
  </section>
</uscDoc>
"""


def _write_uslm_zip(zip_path: Path, xml: bytes = USLM_XML) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("xml_usc99.xml", xml)
    return zip_path


def test_extract_sections_filters_editorial_text_and_allows_missing_sections(
    tmp_path: Path,
) -> None:
    zip_path = _write_uslm_zip(tmp_path / "synthetic-uslm.zip")

    found = extract_sections(zip_path, 99, {"101", "102", "103"})

    assert set(found) == {"101", "102"}
    assert found["101"].identifier == "/us/usc/t99/s101"
    assert found["101"].heading == "Required records"
    assert "\n\n(a) Subsection body text must remain quotable." in found["101"].text
    assert "Source credit must not be quoted." not in found["101"].text
    assert "Editorial note must not be quoted." not in found["101"].text
    assert found["102"].identifier == "/us/usc/t99/s102"
    assert found["102"].heading == "Repealed provision"
    assert found["102"].status == "repealed"
    assert "103" not in found


def test_extract_sections_does_not_clear_parser_buffered_future_sections(
    tmp_path: Path,
) -> None:
    fillers = "".join(f"<meta><value>{index}</value></meta>" for index in range(400))
    buffered_xml = (
        '<uscDoc xmlns="http://xml.house.gov/schemas/uslm/1.0">'
        f"{fillers}"
        '<section identifier="/us/usc/t99/s101">'
        "<heading>Buffered section</heading>"
        "<subsection><content>Future section text survives.</content></subsection>"
        "</section>"
        "</uscDoc>"
    ).encode()
    zip_path = _write_uslm_zip(tmp_path / "buffered-uslm.zip", buffered_xml)

    found = extract_sections(zip_path, 99, {"101"})

    assert found["101"].heading == "Buffered section"
    assert "Future section text survives." in found["101"].text


def test_title_zip_url_formats_title_and_validates_release_point() -> None:
    assert title_zip_url("119-102", 5) == (
        "https://uscode.house.gov/download/releasepoints/us/pl/119/102/xml_usc05@119-102.zip"
    )
    assert title_zip_url("119-102", 31) == (
        "https://uscode.house.gov/download/releasepoints/us/pl/119/102/xml_usc31@119-102.zip"
    )
    with pytest.raises(ValueError):
        title_zip_url("bad", 31)


def _place_cache(cache_path: Path, payload: bytes) -> None:
    """Pre-place a cached archive WITH its digest sidecar (the replay contract)."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(payload)
    cache_path.with_suffix(".zip.sha256").write_text(hashlib.sha256(payload).hexdigest() + "\n")


def test_fetch_title_zip_returns_existing_cache_without_network(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    cache_path = tmp_path / "cache" / "xml_usc05@119-102.zip"
    cached_bytes = b"PK\x03\x04already cached"
    _place_cache(cache_path, cached_bytes)

    result = fetch_title_zip(settings, 5)

    assert result == cache_path
    assert result.read_bytes() == cached_bytes


def test_fetch_title_zip_refuses_tampered_or_undigested_cache(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    cache_path = tmp_path / "cache" / "xml_usc05@119-102.zip"
    # Fail-closed: a cached archive without a recorded digest is refused.
    cache_path.parent.mkdir(parents=True)
    cache_path.write_bytes(b"PK\x03\x04no digest")
    with pytest.raises(ValueError, match="no recorded digest"):
        fetch_title_zip(settings, 5)
    # Fail-closed: a digest mismatch (tampered cache) is refused.
    _place_cache(cache_path, b"PK\x03\x04original")
    cache_path.write_bytes(b"PK\x03\x04tampered!")
    with pytest.raises(ValueError, match="digest mismatch"):
        fetch_title_zip(settings, 5)


def test_snapshot_sections_writes_two_idempotent_snapshots_per_found_section(
    tmp_path: Path,
) -> None:
    settings = Settings(data_dir=tmp_path)
    cache_path = tmp_path / "cache" / "xml_usc99@119-102.zip"
    _write_uslm_zip(cache_path)
    _place_cache(cache_path, cache_path.read_bytes())

    first = snapshot_sections(settings, 99, {"101", "102", "103"})

    assert set(first) == {"101", "102"}
    raw_root = tmp_path / "raw"
    initial_snapshot_dirs = set(raw_root.iterdir())
    assert len(initial_snapshot_dirs) == 4
    for section, text_dir in first.items():
        text_path = text_dir / f"usc-99-s{section}.txt"
        json_paths = list(raw_root.glob(f"*/usc-99-s{section}.json"))
        assert text_path.is_file()
        assert len(json_paths) == 1
        json_dir = json_paths[0].parent
        assert json_dir != text_dir
        assert read_manifest(text_dir).content_type == "text/x-usc-section"
        assert read_manifest(json_dir).content_type == "application/x-usc-section+json"

    second = snapshot_sections(settings, 99, {"101", "102", "103"})

    assert second == first
    assert set(raw_root.iterdir()) == initial_snapshot_dirs
