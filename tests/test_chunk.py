"""Chunking bounds every chunk and preserves content and provenance boundaries."""

from hypothesis import given
from hypothesis import strategies as st

from reglens.extract.chunk import chunk_plan_sha256, chunk_text
from reglens.provenance import normalize, verify_span


def _non_empty_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def test_paragraph_is_kept_when_accounted_length_exactly_equals_limit() -> None:
    max_chars = (len("alpha") + 2) + (len("beta") + 2)

    assert chunk_text("alpha\n\nbeta\n\ntail", max_chars=max_chars) == [
        "alpha\n\nbeta",
        "tail",
    ]


def test_oversized_paragraph_is_split_rather_than_emitted_whole() -> None:
    max_chars = 12
    chunks = chunk_text("\n\n".join(["alpha", "beta", "x" * 13, "tail"]), max_chars=max_chars)

    assert chunks == ["alpha\n\nbeta", "x" * 12, "x\n\ntail"]


def test_indivisible_run_is_hard_sliced_to_fit() -> None:
    max_chars = 10

    assert chunk_text("x" * 21, max_chars=max_chars) == ["x" * 10, "x" * 10, "x"]


def test_long_paragraph_splits_at_sentence_boundaries_before_words() -> None:
    text = "Alpha beta gamma. Delta epsilon zeta. Eta theta iota."
    chunks = chunk_text(text, max_chars=30)

    # Each chunk ends at a sentence boundary, so no sentence is cut mid-way.
    assert chunks == ["Alpha beta gamma.", " Delta epsilon zeta.", " Eta theta iota."]


def test_paragraph_breaks_are_not_invented_inside_a_split_paragraph() -> None:
    paragraph = "Alpha beta gamma delta. Epsilon zeta eta theta."
    chunks = chunk_text(paragraph, max_chars=25)

    assert len(chunks) > 1
    assert all("\n\n" not in chunk for chunk in chunks)


def test_rejoining_chunks_preserves_non_empty_paragraphs_once_and_in_order() -> None:
    text = " first paragraph \n\n\n\nsecond paragraph\n\n   \n\nthird"
    chunks = chunk_text(text, max_chars=20)

    assert _non_empty_paragraphs("\n\n".join(chunks)) == _non_empty_paragraphs(text)


def test_whitespace_only_content_is_dropped_only_when_its_chunk_is_empty() -> None:
    assert chunk_text("  \n\n\t\n\n\r ", max_chars=100) == []

    mixed_text = "alpha\n\n   \n\nbeta"
    assert chunk_text(mixed_text, max_chars=100) == [mixed_text]


@given(
    text=st.text(max_size=300),
    max_chars=st.integers(min_value=1, max_value=100),
)
def test_no_chunk_ever_exceeds_the_limit(text: str, max_chars: int) -> None:
    assert all(len(chunk) <= max_chars for chunk in chunk_text(text, max_chars=max_chars))


def _visible(text: str) -> str:
    """Every non-whitespace character, in order — what survives chunk boundaries."""
    return "".join(char for char in text if not char.isspace())


@given(
    text=st.text(max_size=300),
    max_chars=st.integers(min_value=1, max_value=100),
)
def test_chunking_loses_duplicates_and_reorders_nothing(text: str, max_chars: int) -> None:
    """Content is preserved exactly; only whitespace at chunk seams may differ.

    Whitespace is the one thing chunking may change (a paragraph break is
    dropped where it coincides with a chunk break), and it is also the one
    thing the provenance gate normalizes away, so quotes still verify.
    """
    assert _visible("".join(chunk_text(text, max_chars=max_chars))) == _visible(text)


def test_the_chunk_plan_hash_distinguishes_boundaries_the_input_hash_cannot() -> None:
    """Same text, different split, different run — the whole point of the field."""
    text = "Alpha beta gamma. Delta epsilon zeta. Eta theta iota."

    assert chunk_plan_sha256(chunk_text(text, max_chars=30)) != chunk_plan_sha256(
        chunk_text(text, max_chars=1000)
    )
    assert chunk_plan_sha256(chunk_text(text, max_chars=30)) == chunk_plan_sha256(
        chunk_text(text, max_chars=30)
    )


def test_the_chunk_plan_hash_is_order_sensitive() -> None:
    """Chunk order is part of the run: reordering must not look like the same plan."""
    chunks = ["first", "second", "third"]

    assert chunk_plan_sha256(chunks) != chunk_plan_sha256(list(reversed(chunks)))
    assert chunk_plan_sha256(chunks) != chunk_plan_sha256(["firstsecond", "third"])


def test_a_quote_spanning_a_chunk_seam_still_verifies_against_the_source() -> None:
    """The reason splitting below paragraph level is safe (gate normalizes whitespace)."""
    source = "The agency shall submit a report. " * 4
    chunks = chunk_text(source, max_chars=40)
    assert len(chunks) > 1

    spanning_quote = normalize(chunks[0])[-20:] + " " + normalize(chunks[1])[:20]

    assert verify_span(source, spanning_quote).accepted
