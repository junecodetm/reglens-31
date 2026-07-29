"""Tests for the committed rejected-claim comparison and provenance example."""

from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt, StrictStr

from reglens.extract.records import ClaimRecord, DocumentExtraction, load_extractions
from reglens.provenance import normalize

REPO_ROOT = Path(__file__).parents[1]
DATA_DIR = REPO_ROOT / "web" / "public" / "data"
CLAIMS_PATH = DATA_DIR / "claims.json"
DOCUMENTS_DIR = DATA_DIR / "documents"

_DiffKind = Literal["equal", "model", "source"]


class _RejectedDetail(BaseModel):
    """A validated rejected-claim comparison read from committed exporter output."""

    model_config = ConfigDict(extra="forbid")

    similarity: StrictFloat
    closest: None = None
    closest_start: StrictInt | None = None
    closest_end: StrictInt | None = None
    closest_quote: StrictStr | None = None
    diff: list[list[StrictStr]] | None = None


class _RejectedDetailsPayload(BaseModel):
    """The validated shape of the committed rejected-details export."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    method: StrictStr
    details: dict[StrictStr, _RejectedDetail]


class _AcceptedExample(BaseModel):
    """The validated accepted side of the committed provenance example."""

    model_config = ConfigDict(extra="forbid")

    claim_id: StrictStr
    document_number: StrictStr
    document_title: StrictStr
    summary: StrictStr
    quote: StrictStr
    excerpt: StrictStr
    span_start: StrictInt
    span_end: StrictInt


class _RejectedExample(_RejectedDetail):
    """The validated rejected side of the committed provenance example."""

    claim_id: StrictStr
    document_number: StrictStr
    document_title: StrictStr
    summary: StrictStr
    quote: StrictStr


class _ExamplePayload(BaseModel):
    """The validated shape of the committed provenance example export."""

    model_config = ConfigDict(extra="forbid")

    accepted: _AcceptedExample
    rejected: _RejectedExample


def _load_claims() -> list[DocumentExtraction]:
    """Return committed claim extractions; missing or malformed JSON raises."""
    return load_extractions(CLAIMS_PATH)


def _claims_by_id(extractions: list[DocumentExtraction]) -> dict[str, ClaimRecord]:
    """Index claims by id; duplicate ids fail the test instead of being overwritten."""
    result: dict[str, ClaimRecord] = {}
    for extraction in extractions:
        for claim in extraction.claims:
            assert claim.claim_id not in result
            result[claim.claim_id] = claim
    return result


def _load_rejected_details() -> _RejectedDetailsPayload:
    """Return validated rejected details; missing or malformed output raises."""
    return _RejectedDetailsPayload.model_validate_json(
        (DATA_DIR / "rejected-details.json").read_text(encoding="utf-8")
    )


def _load_example() -> _ExamplePayload:
    """Return the validated example; missing or malformed output raises."""
    return _ExamplePayload.model_validate_json(
        (DATA_DIR / "example.json").read_text(encoding="utf-8")
    )


def _has_closest_passage(detail: _RejectedDetail) -> bool:
    """Return whether all passage fields exist; partial entries fail the test."""
    passage_fields = (
        detail.closest_start,
        detail.closest_end,
        detail.closest_quote,
        detail.diff,
    )
    assert all(value is not None for value in passage_fields) or all(
        value is None for value in passage_fields
    )
    return detail.closest_start is not None


def _diff_reconstructions(diff: list[list[str]]) -> tuple[list[str], list[str]]:
    """Reconstruct model/source words; malformed operation pairs fail the test."""
    parsed_ops: list[tuple[_DiffKind, str]] = []
    for operation in diff:
        assert len(operation) == 2
        kind, text = operation
        assert kind in {"equal", "model", "source"}
        parsed_ops.append((cast(_DiffKind, kind), text))

    model_text = " ".join(text for kind, text in parsed_ops if kind in {"equal", "model"})
    source_text = " ".join(text for kind, text in parsed_ops if kind in {"equal", "source"})
    return model_text.split(" "), source_text.split(" ")


def _assert_closest_invariants(
    detail: _RejectedDetail,
    claim: ClaimRecord,
    document_text: str,
) -> None:
    """Assert span, similarity, and diff invariants for one detailed comparison."""
    assert _has_closest_passage(detail)
    assert detail.closest_start is not None
    assert detail.closest_end is not None
    assert detail.closest_quote is not None
    assert detail.diff is not None

    assert 0 <= detail.closest_start < detail.closest_end <= len(document_text)
    assert (
        normalize(document_text[detail.closest_start : detail.closest_end]) == detail.closest_quote
    )
    assert isinstance(detail.similarity, float)
    assert 0.0 <= detail.similarity <= 1.0

    model_words, source_words = _diff_reconstructions(detail.diff)
    assert model_words == normalize(claim.quote).split(" ")
    assert source_words == detail.closest_quote.split(" ")


def test_details_keys_equal_all_rejected_claim_ids() -> None:
    """Every rejected claim appears exactly once, and no accepted claim appears."""
    extractions = _load_claims()
    rejected_ids = {
        claim.claim_id
        for extraction in extractions
        for claim in extraction.claims
        if not claim.accepted
    }

    assert set(_load_rejected_details().details) == rejected_ids


def test_closest_passages_map_to_source_and_reconstruct_both_sides() -> None:
    """Detailed comparisons map to source offsets and losslessly reconstruct both sides."""
    claims = _claims_by_id(_load_claims())

    for claim_id, detail in _load_rejected_details().details.items():
        if not _has_closest_passage(detail):
            continue
        claim = claims[claim_id]
        document_text = (DOCUMENTS_DIR / f"{claim.document_number}.txt").read_text(encoding="utf-8")
        _assert_closest_invariants(detail, claim, document_text)


def test_entries_without_closest_passages_are_below_threshold() -> None:
    """Absent closest passages are allowed only below the 0.35 cutoff."""
    for detail in _load_rejected_details().details.values():
        if _has_closest_passage(detail):
            continue
        assert detail.closest is None
        assert 0.0 <= detail.similarity < 0.35


def test_example_uses_pinned_claims_and_valid_provenance() -> None:
    """The static example pins one real acceptance and one real rejection."""
    claims = _claims_by_id(_load_claims())
    example = _load_example()

    assert example.accepted.claim_id == "fe677d4f490f99b2"
    accepted_claim = claims[example.accepted.claim_id]
    assert accepted_claim.accepted is True
    assert example.accepted.document_number == accepted_claim.document_number
    assert accepted_claim.start is not None
    assert accepted_claim.end is not None
    accepted_document_text = (DOCUMENTS_DIR / f"{accepted_claim.document_number}.txt").read_text(
        encoding="utf-8"
    )
    assert (
        0
        <= example.accepted.span_start
        < example.accepted.span_end
        <= len(example.accepted.excerpt)
    )
    assert (
        example.accepted.excerpt[example.accepted.span_start : example.accepted.span_end]
        == accepted_document_text[accepted_claim.start : accepted_claim.end]
    )

    assert example.rejected.claim_id == "33961b9a82254639"
    rejected_claim = claims[example.rejected.claim_id]
    assert rejected_claim.accepted is False
    assert example.rejected.document_number == rejected_claim.document_number
    if _has_closest_passage(example.rejected):
        rejected_document_text = (
            DOCUMENTS_DIR / f"{rejected_claim.document_number}.txt"
        ).read_text(encoding="utf-8")
        _assert_closest_invariants(example.rejected, rejected_claim, rejected_document_text)
    else:
        assert example.rejected.similarity < 0.35
