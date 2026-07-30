"""Paragraph chunking preserves content and provenance boundaries."""

from hypothesis import given
from hypothesis import strategies as st

from reglens.extract.chunk import chunk_text


def _non_empty_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def test_chunks_stay_within_limit_except_for_one_oversized_paragraph() -> None:
    max_chars = 12
    paragraphs = ["alpha", "beta", "x" * (max_chars + 1), "tail"]
    chunks = chunk_text("\n\n".join(paragraphs), max_chars=max_chars)

    assert chunks == ["alpha", "beta", "x" * 13, "tail"]


def test_paragraph_is_kept_when_accounted_length_exactly_equals_limit() -> None:
    max_chars = (len("alpha") + 2) + (len("beta") + 2)

    assert chunk_text("alpha\n\nbeta\n\ntail", max_chars=max_chars) == [
        "alpha\n\nbeta",
        "tail",
    ]


def test_rejoining_chunks_preserves_non_empty_paragraphs_once_and_in_order() -> None:
    text = " first paragraph \n\n\n\nsecond paragraph\n\n   \n\nthird"
    chunks = chunk_text(text, max_chars=20)

    assert _non_empty_paragraphs("\n\n".join(chunks)) == _non_empty_paragraphs(text)


def test_single_oversized_paragraph_is_returned_unchanged() -> None:
    max_chars = 10
    paragraph = "x" * (max_chars + 1)

    assert chunk_text(paragraph, max_chars=max_chars) == [paragraph]


def test_whitespace_only_content_is_dropped_only_when_its_chunk_is_empty() -> None:
    assert chunk_text("  \n\n\t\n\n\r ", max_chars=100) == []

    mixed_text = "alpha\n\n   \n\nbeta"
    assert chunk_text(mixed_text, max_chars=100) == [mixed_text]


@given(
    text=st.text(max_size=300),
    max_chars=st.integers(min_value=1, max_value=100),
)
def test_chunking_preserves_non_empty_stripped_paragraphs(text: str, max_chars: int) -> None:
    rejoined = "\n\n".join(chunk_text(text, max_chars=max_chars))

    assert _non_empty_paragraphs(rejoined) == _non_empty_paragraphs(text)
