"""Provision sampling keeps exact offsets and deterministic selection."""

import hashlib
from collections import Counter

from reglens.eval.provisions import (
    MAX_CHARS,
    MIN_CHARS,
    candidate_paragraphs,
    sample_provisions,
)
from reglens.extract.run import DocumentPair


def _pair(document_number: str, paragraph_count: int) -> DocumentPair:
    paragraphs: list[str] = []
    for index in range(paragraph_count):
        prefix = f"{document_number}-{index:02d} "
        paragraphs.append(prefix + "x" * (MIN_CHARS - len(prefix)))
    text = "\n\n".join(paragraphs)
    return DocumentPair(
        document_number=document_number,
        title=f"Title {document_number}",
        url=f"https://www.federalregister.gov/documents/{document_number}",
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        text=text,
    )


def test_candidate_paragraph_spans_are_exact_stripped_source_slices() -> None:
    paragraphs = [
        "too short",
        " \t" + "a" * MIN_CHARS + "  ",
        "\n" + "b" * (MIN_CHARS + 25) + "\t",
    ]
    text = "\n\n".join(paragraphs)
    pair = DocumentPair("DOC", "Title", "https://example.test", "0" * 64, text)
    qualifying = ["a" * MIN_CHARS, "b" * (MIN_CHARS + 25)]
    spans = candidate_paragraphs(pair)

    assert len(spans) == len(qualifying)
    for paragraph, (start, end) in zip(qualifying, spans, strict=True):
        assert text[start:end] == paragraph


def test_candidate_paragraphs_tracks_distinct_offsets_for_identical_paragraphs() -> None:
    prefix = "repeated "
    paragraph = prefix + "x" * (MIN_CHARS - len(prefix))
    text = "\n\n".join([paragraph, paragraph])
    pair = DocumentPair("DOC", "Title", "https://example.test", "0" * 64, text)

    spans = candidate_paragraphs(pair)

    assert spans == [
        (0, len(paragraph)),
        (len(paragraph) + 2, len(text)),
    ]
    assert spans[0][0] != spans[1][0]
    assert [text[start:end] for start, end in spans] == [paragraph, paragraph]


def test_candidate_paragraph_boundaries_are_inclusive_and_exclusive() -> None:
    paragraphs = [
        "a" * (MIN_CHARS - 1),
        "b" * MIN_CHARS,
        "c" * MAX_CHARS,
        "d" * (MAX_CHARS + 1),
    ]
    pair = DocumentPair(
        "DOC",
        "Title",
        "https://example.test",
        "0" * 64,
        "\n\n".join(paragraphs),
    )

    slices = [pair.text[start:end] for start, end in candidate_paragraphs(pair)]

    assert slices == ["b" * MIN_CHARS, "c" * MAX_CHARS]


def test_sample_provisions_is_seeded_and_different_seeds_change_the_set() -> None:
    pair = _pair("DOC-A", paragraph_count=12)

    first = sample_provisions([pair], per_document=5, seed=31)
    repeated = sample_provisions([pair], per_document=5, seed=31)
    different = sample_provisions([pair], per_document=5, seed=32)

    assert [item.provision_id for item in first] == [item.provision_id for item in repeated]
    assert {item.provision_id for item in first} != {item.provision_id for item in different}


def test_sample_provisions_honors_the_per_document_cap() -> None:
    sampled = sample_provisions(
        [_pair("DOC-A", paragraph_count=5), _pair("DOC-B", paragraph_count=2)],
        per_document=3,
    )

    assert Counter(item.document_number for item in sampled) == {
        "DOC-A": 3,
        "DOC-B": 2,
    }
    starts_by_document = {
        document_number: [item.start for item in sampled if item.document_number == document_number]
        for document_number in ("DOC-A", "DOC-B")
    }
    for starts in starts_by_document.values():
        assert starts == sorted(starts)
