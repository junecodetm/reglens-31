"""Fail-closed provenance gate (PROVENANCE-GATE INVARIANT, CLAUDE.md §2, invariant 2).

Inputs: the full source text and one claimed verbatim quote. Outputs: a
:class:`VerificationResult` — accepted with exact character offsets into the
original source, or rejected with a reason. Failure mode: ANY inability to
verify (empty quote, no match, internal error) rejects the claim. Nothing is
ever accepted without an exact normalized-substring match.

Documented normalization (applied identically to source and quote):
1. Each character is Unicode-normalized with NFKC, character by character
   (so NBSP becomes a space, ligatures expand, fullwidth forms fold).
2. Every run of whitespace collapses to a single ASCII space.
3. Leading/trailing whitespace is dropped.
Character-by-character NFKC is deliberate: it lets every normalized character
carry the index of the original character that produced it, so an accepted
quote maps back to exact highlight offsets in the untouched source text. Both
sides of the comparison use this same transform, so the comparison is
consistent even where per-character NFKC differs from whole-string NFKC
(combining sequences).
"""

import unicodedata

from pydantic import BaseModel


class VerificationResult(BaseModel):
    """Outcome of verifying one quote against one source text."""

    accepted: bool
    start: int | None = None
    end: int | None = None
    reason: str | None = None


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalized text plus, per normalized character, the originating original index."""
    out_chars: list[str] = []
    index_map: list[int] = []
    pending_space_index: int | None = None
    for original_index, char in enumerate(text):
        for normalized_char in unicodedata.normalize("NFKC", char):
            if normalized_char.isspace():
                if pending_space_index is None:
                    pending_space_index = original_index
                continue
            if pending_space_index is not None:
                if out_chars:  # leading whitespace is dropped, not emitted
                    out_chars.append(" ")
                    index_map.append(pending_space_index)
                pending_space_index = None
            out_chars.append(normalized_char)
            index_map.append(original_index)
    # Trailing whitespace is dropped by never emitting a pending space at the end.
    return "".join(out_chars), index_map


def normalize(text: str) -> str:
    """The documented normalization, exposed for tests and the eval harness."""
    return _normalize_with_map(text)[0]


def verify_span(source_text: str, quote: str) -> VerificationResult:
    """Accept ``quote`` iff its normalized form is an exact substring of the normalized source.

    Accepted results carry ``[start, end)`` character offsets into the ORIGINAL
    ``source_text`` covering the first match. Rejections carry a reason and are
    final — there is no retry or fuzzy fallback (fail-closed).
    """
    try:
        normalized_quote = normalize(quote)
        if not normalized_quote:
            # Fail-closed: an empty or whitespace-only quote verifies nothing.
            return VerificationResult(accepted=False, reason="empty-quote")
        normalized_source, index_map = _normalize_with_map(source_text)
        match_start = normalized_source.find(normalized_quote)
        if match_start == -1:
            # Fail-closed: the claim's quote is not present verbatim in the source.
            return VerificationResult(accepted=False, reason="not-a-substring")
        match_end = match_start + len(normalized_quote) - 1
        return VerificationResult(
            accepted=True,
            start=index_map[match_start],
            end=index_map[match_end] + 1,
        )
    except Exception:
        # Fail-closed: if verification cannot run, the claim is dropped, not kept.
        return VerificationResult(accepted=False, reason="verification-error")
