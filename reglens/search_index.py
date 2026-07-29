(
    "Build a deterministic, self-contained search index from typed source text.\n\n"
    "NFKC-normalize, casefold, then tokens = regex "
    r"[a-z0-9]+(?:\.[a-z0-9]+)* -- dots survive only inside tokens "
    '(so "31 U.S.C. 321" becomes ["31","u.s.c","321"] and the '
    'section-designation "501.101" style stays as a single token "501.101").\n\n'
    "Inputs are ordered ``SearchSource`` records. Outputs are a pure ``SearchIndex`` model "
    "and, optionally, its compact deterministic JSON representation. Invalid model relationships "
    "raise Pydantic validation errors; serialization raises ``ValueError`` for invalid numeric "
    "JSON or excess bytes and may raise ``UnicodeEncodeError`` for invalid Unicode surrogates."
)

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from typing import Annotated, Final, Literal, Self

from pydantic import BaseModel, Field, model_validator

MAX_INDEX_BYTES: Final = 4 * 1024 * 1024
TOKENIZER_SPEC: Final = (
    "NFKC-normalize, casefold, then tokens = regex "
    "[a-z0-9]+(?:\\.[a-z0-9]+)* -- dots survive only inside tokens"
)

_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"[a-z0-9]+(?:\.[a-z0-9]+)*",
    flags=re.ASCII,
)
_NonNegativeInt = Annotated[int, Field(ge=0)]
_PositiveInt = Annotated[int, Field(gt=0)]


class CfrSectionRef(BaseModel):
    """A CFR part and nonempty half-open section range.

    Inputs:
        ``part`` is the nonnegative CFR part; ``start`` and ``end`` delimit ``[start, end)``.
    Output:
        A structured reference suitable for a ``cfr-section`` search source or unit.
    Failure mode:
        Pydantic raises ``ValidationError`` for negative values or ``end <= start``.
    """

    part: int = Field(ge=0)
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        """Require a nonempty half-open section range and return the validated model."""
        if self.end <= self.start:
            raise ValueError("end must be greater than start for half-open range [start, end)")
        return self


class SearchSource(BaseModel):
    """An ordered source record containing searchable text and display metadata.

    Inputs:
        Identity, source type, label, type-appropriate reference, and full source text.
    Output:
        A validated input record accepted by ``build_search_index``.
    Failure mode:
        Pydantic raises ``ValidationError`` when fields or the reference shape are invalid.
    """

    id: str
    type: Literal["claim", "usc", "cfr-section", "draft"]
    label: str
    ref: str | CfrSectionRef
    text: str

    @model_validator(mode="after")
    def validate_ref_shape(self) -> Self:
        """Require structured CFR references and string references for every other type."""
        if self.type == "cfr-section" and not isinstance(self.ref, CfrSectionRef):
            raise ValueError("cfr-section sources require a CfrSectionRef")
        if self.type != "cfr-section" and not isinstance(self.ref, str):
            raise ValueError(f"{self.type} sources require a string ref")
        return self


class SearchUnit(BaseModel):
    """Emitted metadata for one indexed source, excluding its full source text.

    Inputs:
        Source metadata, type-appropriate reference, token length, and collapsed snippet.
    Output:
        A validated unit stored in ``SearchIndex.units``.
    Failure mode:
        Pydantic raises ``ValidationError`` for negative length or an invalid reference shape.
    """

    id: str
    type: Literal["claim", "usc", "cfr-section", "draft"]
    label: str
    ref: str | CfrSectionRef
    length: int = Field(ge=0)
    snippet: str

    @model_validator(mode="after")
    def validate_ref_shape(self) -> Self:
        """Require structured CFR references and string references for every other type."""
        if self.type == "cfr-section" and not isinstance(self.ref, CfrSectionRef):
            raise ValueError("cfr-section units require a CfrSectionRef")
        if self.type != "cfr-section" and not isinstance(self.ref, str):
            raise ValueError(f"{self.type} units require a string ref")
        return self


class SearchIndex(BaseModel):
    """A deterministic inverted index and ordered search-unit metadata.

    Inputs:
        Tokenizer contract, finite average length, ordered units, and token posting lists.
        Each posting is ``(unit_index, term_frequency)`` with a positive frequency. Within
        each token list, unit indexes are unique, in range, and strictly ascending.
    Output:
        A validated, serialization-ready search index.
    Failure mode:
        Pydantic raises ``ValidationError`` for invalid numbers or inconsistent postings.
    """

    tokenizer: str
    avgdl: float = Field(ge=0.0, allow_inf_nan=False)
    units: list[SearchUnit]
    postings: dict[str, list[tuple[_NonNegativeInt, _PositiveInt]]]

    @model_validator(mode="after")
    def validate_postings(self) -> Self:
        """Require every posting list to contain ordered indexes into ``units``."""
        unit_count = len(self.units)
        for token, posting_list in self.postings.items():
            previous_unit_index = -1
            for unit_index, _term_frequency in posting_list:
                if unit_index >= unit_count:
                    raise ValueError(
                        f"posting for {token!r} has unit index {unit_index}, "
                        f"but only {unit_count} units exist"
                    )
                if unit_index <= previous_unit_index:
                    raise ValueError(f"posting indexes for {token!r} must be strictly ascending")
                previous_unit_index = unit_index
        return self


def tokenize(text: str) -> list[str]:
    """Normalize source text and extract all tokenizer-contract matches.

    Inputs:
        text: Source text to NFKC-normalize and casefold.

    Returns:
        Tokens in their source order, including repeated words and without stopword removal.

    Raises:
        TypeError: If ``text`` is not a string.
    """

    normalized = unicodedata.normalize("NFKC", text).casefold()
    return _TOKEN_RE.findall(normalized)


def build_search_index(sources: Sequence[SearchSource]) -> SearchIndex:
    """Build an ordered inverted index from validated source records.

    Inputs:
        sources: Search sources in the order their units should be emitted.

    Returns:
        A search index with sorted posting keys, term frequencies, snippets, and mean length.

    Raises:
        TypeError: If a source bypassed model validation and contains non-string text.
    """

    units: list[SearchUnit] = []
    postings_by_token: dict[str, list[tuple[int, int]]] = {}

    for unit_index, source in enumerate(sources):
        tokens = tokenize(source.text)
        units.append(
            SearchUnit(
                id=source.id,
                type=source.type,
                label=source.label,
                ref=source.ref,
                length=len(tokens),
                snippet=" ".join(source.text.split())[:160],
            )
        )
        for token, term_frequency in Counter(tokens).items():
            postings_by_token.setdefault(token, []).append((unit_index, term_frequency))

    postings = {token: postings_by_token[token] for token in sorted(postings_by_token)}
    avgdl = sum(unit.length for unit in units) / len(units) if units else 0.0
    return SearchIndex(
        tokenizer=TOKENIZER_SPEC,
        avgdl=avgdl,
        units=units,
        postings=postings,
    )


def serialize_search_index(
    index: SearchIndex,
    *,
    max_bytes: int = MAX_INDEX_BYTES,
) -> str:
    """Serialize an index deterministically after enforcing its exact UTF-8 size.

    Inputs:
        index: The typed search index to serialize.
        max_bytes: Maximum permitted byte length, including the trailing newline.

    Returns:
        Compact, key-sorted UTF-8 JSON text terminated by one newline.

    Raises:
        ValueError: If JSON contains a nonfinite number or exceeds ``max_bytes`` after encoding.
        UnicodeEncodeError: If string data contains a surrogate that cannot be encoded as UTF-8.
    """

    serialized = (
        json.dumps(
            index.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    actual_bytes = len(serialized.encode("utf-8"))
    if actual_bytes > max_bytes:
        raise ValueError(
            f"Search index is {actual_bytes} UTF-8 bytes, exceeding the {max_bytes}-byte "
            f"limit (default 4 MiB / {MAX_INDEX_BYTES} bytes); no output was truncated."
        )
    return serialized
