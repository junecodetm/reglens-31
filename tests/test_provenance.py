"""The provenance gate: fabricated quotes die, real quotes map to exact offsets."""

from hypothesis import given
from hypothesis import strategies as st

from reglens.provenance import normalize, verify_span

SOURCE = (
    "Sec. 1010.100 Definitions.\n\n"
    "Each financial institution\u00a0must file a report within 30 days.\n"
    "No person may structure transactions to evade the requirements of this part."
)


def test_fabricated_quote_is_rejected() -> None:
    result = verify_span(SOURCE, "Each person must notify the Secretary within 10 days.")
    assert not result.accepted
    assert result.reason == "not-a-substring"
    assert result.start is None and result.end is None


def test_verbatim_quote_is_accepted_with_original_offsets() -> None:
    quote = "No person may structure transactions"
    result = verify_span(SOURCE, quote)
    assert result.accepted
    assert result.start is not None and result.end is not None
    assert SOURCE[result.start : result.end] == quote


def test_whitespace_and_nbsp_variants_still_verify() -> None:
    # Source has an NBSP between "institution" and "must"; quote uses plain spaces + newline.
    quote = "Each financial institution must file\na report   within 30 days."
    result = verify_span(SOURCE, quote)
    assert result.accepted
    assert result.start is not None and result.end is not None
    assert normalize(SOURCE[result.start : result.end]) == normalize(quote)


def test_empty_and_whitespace_quotes_are_rejected() -> None:
    assert verify_span(SOURCE, "").reason == "empty-quote"
    assert verify_span(SOURCE, "  \n\t ").reason == "empty-quote"


def test_empty_source_rejects_any_quote() -> None:
    result = verify_span("", "Each person must file.")
    assert not result.accepted
    assert result.reason == "not-a-substring"


def test_quote_longer_than_source_is_rejected() -> None:
    result = verify_span("Short text.", "Short text. And much more that is not there.")
    assert not result.accepted
    assert result.reason == "not-a-substring"


def test_ligature_folding() -> None:
    # NFKC expands the "ﬁ" ligature, so a ligature quote matches its expanded source form.
    source = "The bank must file annually."
    assert verify_span(source, "must ﬁle annually").accepted


@given(st.text())
def test_normalize_is_idempotent(text: str) -> None:
    assert normalize(normalize(text)) == normalize(text)


@given(st.text())
def test_normalize_has_no_edge_or_double_spaces(text: str) -> None:
    normalized = normalize(text)
    assert normalized == normalized.strip()
    assert "  " not in normalized


@given(st.data())
def test_any_true_substring_verifies_and_offsets_cover_it(data: st.DataObject) -> None:
    source = data.draw(st.text(alphabet=st.characters(codec="ascii"), min_size=1, max_size=200))
    start = data.draw(st.integers(min_value=0, max_value=len(source) - 1))
    end = data.draw(st.integers(min_value=start + 1, max_value=len(source)))
    quote = source[start:end]
    result = verify_span(source, quote)
    if normalize(quote):
        assert result.accepted
        assert result.start is not None and result.end is not None
        assert normalize(source[result.start : result.end]) == normalize(quote)
    else:
        # Whitespace-only slices verify nothing — fail-closed.
        assert not result.accepted


@given(
    st.text(alphabet=st.characters(codec="ascii"), min_size=1, max_size=200),
    st.text(alphabet="0123456789", min_size=1, max_size=20),
)
def test_quotes_absent_from_source_are_rejected(source_letters: str, digits: str) -> None:
    source = source_letters.replace(digits, "") if digits in source_letters else source_letters
    fabricated = f"zz{digits}zz"
    if fabricated in source:  # pragma: no cover - safeguarded improbable draw
        return
    assert not verify_span(source, fabricated).accepted
