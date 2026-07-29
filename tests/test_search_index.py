"""Tests for the deterministic pure-Python search index."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pytest
from pydantic import ValidationError

from reglens.search_index import (
    MAX_INDEX_BYTES,
    TOKENIZER_SPEC,
    CfrSectionRef,
    SearchIndex,
    SearchSource,
    SearchUnit,
    build_search_index,
    serialize_search_index,
    tokenize,
)


def test_tokenize_preserves_legal_citation_tokens() -> None:
    """Legal abbreviations and decimal-style section designations retain internal dots."""
    assert tokenize("31 U.S.C. 321") == ["31", "u.s.c", "321"]
    assert tokenize("§ 501.101") == ["501.101"]


def test_tokenize_applies_nfkc_before_casefolding() -> None:
    """Compatibility-width and case variants normalize deterministically."""
    assert tokenize("\uff26\uff2f\uff2f Straße") == ["foo", "strasse"]


def test_tokenizer_contract_is_exposed_verbatim() -> None:
    """Callers can publish the exact tokenizer contract alongside the index."""
    expected = (
        "NFKC-normalize, casefold, then tokens = regex "
        "[a-z0-9]+(?:\\.[a-z0-9]+)* -- dots survive only inside tokens"
    )
    full_sentence = (
        f'{expected} (so "31 U.S.C. 321" becomes ["31","u.s.c","321"] and the '
        'section-designation "501.101" style stays as a single token "501.101").'
    )

    assert expected == TOKENIZER_SPEC
    assert full_sentence in (__import__("reglens.search_index", fromlist=[""]).__doc__ or "")


def test_build_search_index_preserves_order_and_computes_units_and_postings() -> None:
    """Index construction emits ordered metadata, snippets, frequencies, and mean length."""
    long_text = "Bank  bank\ncompliance " + ("tail " * 40)
    sources = [
        SearchSource(
            id="claim-1",
            type="claim",
            label="Claim one",
            ref="claim:1",
            text="The  bank\n\tacts. The",
        ),
        SearchSource(
            id="cfr-501",
            type="cfr-section",
            label="31 CFR 501",
            ref=CfrSectionRef(part=501, start=101, end=102),
            text=long_text,
        ),
    ]

    index = build_search_index(sources)

    assert [unit.id for unit in index.units] == ["claim-1", "cfr-501"]
    assert [unit.length for unit in index.units] == [4, 43]
    assert index.units[0].snippet == "The bank acts. The"
    assert index.units[1].snippet == " ".join(long_text.split())[:160]
    assert index.avgdl == 23.5
    assert list(index.postings) == sorted(index.postings)
    assert index.postings["bank"] == [(0, 1), (1, 2)]
    assert index.postings["tail"] == [(1, 40)]
    assert index.postings["the"] == [(0, 2)]
    assert index.units[1].model_dump(mode="json")["ref"] == {
        "part": 501,
        "start": 101,
        "end": 102,
    }


def test_build_search_index_has_zero_average_for_no_sources() -> None:
    """An empty source sequence produces a valid empty index."""
    assert build_search_index([]) == SearchIndex(
        tokenizer=TOKENIZER_SPEC,
        avgdl=0.0,
        units=[],
        postings={},
    )


def test_models_reject_negative_offsets_lengths_and_posting_values() -> None:
    """Typed models reject negative numeric values used by the index format."""
    with pytest.raises(ValidationError):
        CfrSectionRef(part=501, start=-1, end=1)

    with pytest.raises(ValidationError):
        SearchUnit(
            id="unit",
            type="draft",
            label="Unit",
            ref="draft:1",
            length=-1,
            snippet="",
        )

    with pytest.raises(ValidationError):
        SearchIndex(
            tokenizer=TOKENIZER_SPEC,
            avgdl=0.0,
            units=[],
            postings={"term": [(-1, 1)]},
        )

    with pytest.raises(ValidationError):
        SearchIndex(
            tokenizer=TOKENIZER_SPEC,
            avgdl=0.0,
            units=[],
            postings={"term": [(0, -1)]},
        )


def test_cfr_section_ref_requires_a_nonempty_half_open_range() -> None:
    """A CFR reference represents a nonempty half-open ``[start, end)`` range."""
    assert CfrSectionRef(part=501, start=1, end=2).model_dump() == {
        "part": 501,
        "start": 1,
        "end": 2,
    }

    with pytest.raises(ValidationError):
        CfrSectionRef(part=501, start=2, end=1)

    with pytest.raises(ValidationError):
        CfrSectionRef(part=501, start=1, end=1)


def test_cfr_sources_and_units_require_structured_refs() -> None:
    """The CFR source type cannot carry an opaque string reference."""
    with pytest.raises(ValidationError):
        SearchSource(
            id="cfr",
            type="cfr-section",
            label="CFR",
            ref="501:1",
            text="text",
        )

    with pytest.raises(ValidationError):
        SearchUnit(
            id="cfr",
            type="cfr-section",
            label="CFR",
            ref="501:1",
            length=1,
            snippet="text",
        )


@pytest.mark.parametrize("source_type", ["claim", "usc", "draft"])
def test_non_cfr_sources_and_units_require_string_refs(
    source_type: Literal["claim", "usc", "draft"],
) -> None:
    """Every non-CFR source type rejects a structured CFR reference."""
    cfr_ref = CfrSectionRef(part=501, start=1, end=2)

    with pytest.raises(ValidationError):
        SearchSource(
            id="non-cfr",
            type=source_type,
            label="Non-CFR",
            ref=cfr_ref,
            text="text",
        )

    with pytest.raises(ValidationError):
        SearchUnit(
            id="non-cfr",
            type=source_type,
            label="Non-CFR",
            ref=cfr_ref,
            length=1,
            snippet="text",
        )


def test_search_index_requires_positive_term_frequency() -> None:
    """Posting term frequencies cannot be zero."""
    unit = SearchUnit(
        id="unit",
        type="draft",
        label="Unit",
        ref="draft:1",
        length=1,
        snippet="term",
    )

    with pytest.raises(ValidationError):
        SearchIndex(
            tokenizer=TOKENIZER_SPEC,
            avgdl=1.0,
            units=[unit],
            postings={"term": [(0, 0)]},
        )


def test_search_index_rejects_posting_unit_indexes_outside_units() -> None:
    """Every posting unit index must identify an emitted unit."""
    unit = SearchUnit(
        id="unit",
        type="draft",
        label="Unit",
        ref="draft:1",
        length=1,
        snippet="term",
    )

    with pytest.raises(ValidationError):
        SearchIndex(
            tokenizer=TOKENIZER_SPEC,
            avgdl=1.0,
            units=[unit],
            postings={"term": [(1, 1)]},
        )


@pytest.mark.parametrize(
    "postings",
    [
        [(1, 1), (0, 1)],
        [(0, 1), (0, 2)],
    ],
)
def test_search_index_requires_strictly_ascending_posting_indexes(
    postings: list[tuple[int, int]],
) -> None:
    """A term's posting list cannot be unordered or contain duplicate unit indexes."""
    units = [
        SearchUnit(
            id=f"unit-{unit_index}",
            type="draft",
            label=f"Unit {unit_index}",
            ref=f"draft:{unit_index}",
            length=1,
            snippet="term",
        )
        for unit_index in range(2)
    ]

    with pytest.raises(ValidationError):
        SearchIndex(
            tokenizer=TOKENIZER_SPEC,
            avgdl=1.0,
            units=units,
            postings={"term": postings},
        )


@pytest.mark.parametrize("avgdl", [float("nan"), float("inf"), float("-inf")])
def test_search_index_rejects_nonfinite_average_lengths(avgdl: float) -> None:
    """Average document length must be a finite number."""
    with pytest.raises(ValidationError):
        SearchIndex(
            tokenizer=TOKENIZER_SPEC,
            avgdl=avgdl,
            units=[],
            postings={},
        )


def test_serializer_rejects_nonfinite_values_if_validation_was_bypassed() -> None:
    """JSON serialization independently rejects non-standard NaN values."""
    invalid_index = SearchIndex.model_construct(
        tokenizer=TOKENIZER_SPEC,
        avgdl=float("nan"),
        units=[],
        postings={},
    )

    with pytest.raises(ValueError, match="Out of range float values"):
        serialize_search_index(invalid_index)


def test_public_model_docstrings_explain_contracts_and_failures() -> None:
    """Public model documentation states its inputs, output, and validation failure mode."""
    for model in (CfrSectionRef, SearchSource, SearchUnit, SearchIndex):
        docstring = model.__doc__ or ""
        assert "Inputs:" in docstring
        assert "Output:" in docstring
        assert "Failure mode:" in docstring

    cfr_docstring = CfrSectionRef.__doc__ or ""
    assert "[start, end)" in cfr_docstring

    index_docstring = SearchIndex.__doc__ or ""
    assert "(unit_index, term_frequency)" in index_docstring
    assert "strictly ascending" in index_docstring


def test_serializer_documents_unicode_encoding_failure() -> None:
    """The serializer documents UTF-8 encoding failures from unpaired surrogates."""
    assert "UnicodeEncodeError" in (serialize_search_index.__doc__ or "")


def test_serialize_search_index_is_compact_deterministic_json() -> None:
    """Identical index values serialize to the same compact newline-terminated JSON."""
    sources = [
        SearchSource(
            id="draft-1",
            type="draft",
            label="Draft",
            ref="draft:1",
            text="The same same text",
        )
    ]
    first_index = build_search_index(sources)
    second_index = build_search_index(sources)

    first = serialize_search_index(first_index)
    second = serialize_search_index(second_index)
    expected = (
        json.dumps(
            first_index.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )

    assert first == second == expected
    assert first.endswith("\n")
    assert '": "' not in first
    assert MAX_INDEX_BYTES == 4 * 1024 * 1024


def test_serialize_search_index_enforces_utf8_byte_limit_without_truncation() -> None:
    """The size guard counts encoded bytes and reports both actual and allowed sizes."""
    index = build_search_index(
        [
            SearchSource(
                id="é",
                type="usc",
                label="é",
                ref="é",
                text="é" * 40,
            )
        ]
    )
    serialized = serialize_search_index(index, max_bytes=10_000)
    actual_bytes = len(serialized.encode("utf-8"))
    character_limit = len(serialized)
    assert actual_bytes > character_limit

    with pytest.raises(ValueError) as exc_info:
        serialize_search_index(index, max_bytes=character_limit)

    message = str(exc_info.value)
    assert str(actual_bytes) in message
    assert str(character_limit) in message


def test_snapshot_payload_path_rejects_directory_escape(tmp_path: Path) -> None:
    """Static export resolves snapshot payloads only from safe basename manifests."""
    from reglens.store.export_web import snapshot_payload_path

    assert snapshot_payload_path(tmp_path, "payload.txt") == tmp_path / "payload.txt"
    with pytest.raises(ValueError, match="Unsafe snapshot filename"):
        snapshot_payload_path(tmp_path, "../payload.txt")
    with pytest.raises(ValueError, match="Unsafe snapshot filename"):
        snapshot_payload_path(tmp_path, "/payload.txt")


def test_real_web_export_writes_sections_and_search_index(tmp_path: Path) -> None:
    """The normal real-data export flow writes both validated static artifacts."""
    from reglens.config import Settings
    from reglens.store.export_web import export_ogc01_data, export_web_data

    required_inputs = (
        Path("data/processed/claims.json"),
        Path("data/processed/authority.json"),
        Path("data/processed/grounding.json"),
        Path("data/processed/conformance.json"),
        Path("data/processed/drafts"),
        Path("data/raw"),
    )
    if not all(path.exists() for path in required_inputs):
        pytest.skip("real export inputs are absent")

    web_dir = tmp_path / "web"
    settings = Settings(data_dir=Path("data"))
    stale_usc_dir = web_dir / "public" / "data" / "usc"
    stale_usc_dir.mkdir(parents=True)
    stale_usc_path = stale_usc_dir / "usc-99-s999.txt"
    stale_usc_path.write_text("Stale authority text.", encoding="utf-8")
    export_web_data(settings, web_dir)
    export_ogc01_data(settings, web_dir)

    out_dir = web_dir / "public" / "data"
    sections_text = (out_dir / "sections.json").read_text(encoding="utf-8")
    search_text = (out_dir / "search-index.json").read_text(encoding="utf-8")
    sections = json.loads(sections_text)
    search_index = json.loads(search_text)

    assert sections["title"] == 31
    assert {part["part"] for part in sections["parts"]} == {50, 223, 285, 356, 501}
    assert all(part["heading"] and part["sections"] for part in sections["parts"])
    assert search_index["tokenizer"] == TOKENIZER_SPEC
    assert {unit["type"] for unit in search_index["units"]} == {
        "claim",
        "usc",
        "cfr-section",
        "draft",
    }
    assert len(search_text.encode("utf-8")) <= MAX_INDEX_BYTES
    assert not stale_usc_path.exists()
    assert all(unit["ref"] != "usc/usc-99-s999.txt" for unit in search_index["units"])
