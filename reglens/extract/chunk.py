"""Boundary-aligned chunking so long documents fit the local model's context.

Inputs: full document text. Outputs: ordered chunks, each at most ``max_chars``
long, split at the coarsest boundary that achieves it — paragraph, then line,
then sentence, then word, and only as a last resort mid-word.

Why the fallbacks exist: eCFR part texts are barely paragraphed (31 CFR 356
carries 53 blank-line breaks across 168,989 characters), so splitting on blank
lines alone produced single chunks of up to 96,431 characters — roughly 24,000
tokens against a 16,384-token context window. Ollama truncates such a prompt
silently, so most of that text was never actually read by the model while
``extracted_chars`` still counted it as covered. Capping every chunk removes
that silent loss.

Splitting finer than a paragraph is safe for provenance: the gate verifies
quotes against the FULL document, not against the chunk, and its normalization
collapses every whitespace run to one space — so a quote spanning a rejoin
boundary still matches. Failure mode: a word longer than ``max_chars`` is cut
mid-word rather than emitted oversized; the gate remains the backstop.
"""

import hashlib
import re
from collections.abc import Sequence
from typing import Final

_BOUNDARIES: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?<=\n)"),  # after a line break
    re.compile(r"(?<=[.!?])(?=\s)"),  # after sentence-ending punctuation
    re.compile(r"(?<=\s)(?=\S)"),  # at the end of any whitespace run
)
"""Split points, coarsest first. All are zero-width, so concatenating the
fragments of a block reproduces that block byte-for-byte."""


def _atoms(block: str, max_chars: int, level: int = 0) -> list[str]:
    """Pieces of ``block``, each at most ``max_chars``, concatenating back to it exactly.

    Descends through :data:`_BOUNDARIES` and hard-slices only when no boundary
    remains, so an indivisible run of characters still yields bounded pieces.
    """
    if len(block) <= max_chars:
        return [block]
    if level >= len(_BOUNDARIES):
        return [block[start : start + max_chars] for start in range(0, len(block), max_chars)]
    parts = _BOUNDARIES[level].split(block)
    if len(parts) <= 1:
        return _atoms(block, max_chars, level + 1)
    return [atom for part in parts for atom in _atoms(part, max_chars, level + 1)]


def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """Split ``text`` into ordered chunks of at most ``max_chars`` characters.

    Paragraph breaks are preserved between chunks; a paragraph too long to fit
    is broken at the finest boundary needed and its pieces are repacked without
    inserting separators that were not there.
    """
    chunks: list[str] = []
    current = ""
    for paragraph_index, paragraph in enumerate(text.split("\n\n")):
        for atom_index, atom in enumerate(_atoms(paragraph, max_chars)):
            separator = "\n\n" if paragraph_index and not atom_index else ""
            if current and len(current) + len(separator) + len(atom) > max_chars:
                chunks.append(current)
                current = atom
            else:
                current = current + separator + atom if current else atom
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk.strip()]


def chunk_plan_sha256(chunks: Sequence[str]) -> str:
    """Identity of the exact chunk sequence a run will send to the model.

    Inputs: the ordered chunks. Output: a hex digest that changes if any chunk's
    text, their order, or their number changes. Failure mode: none — a pure hash.

    Why this exists as its own field rather than folding into the input hash: the
    input hash covers the text a document contributes, not how that text is
    divided, and the model sees one chunk at a time. Two runs over identical text
    with different chunk boundaries are different runs and can differ in output,
    so a determinism record that omits the boundaries cannot support the
    deterministic-replay invariant (CLAUDE.md section 2, invariant 5).
    """
    digest = hashlib.sha256(f"{len(chunks)}".encode())
    for chunk in chunks:
        digest.update(b"\x00")
        digest.update(hashlib.sha256(chunk.encode()).digest())
    return digest.hexdigest()
