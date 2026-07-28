"""Paragraph-boundary chunking so long documents fit the local model's context.

Inputs: full document text. Outputs: ordered chunks, each at most
``max_chars`` long, split only at paragraph boundaries. Failure mode: a single
paragraph longer than ``max_chars`` becomes its own oversized chunk rather
than being split mid-sentence (the provenance gate verifies quotes against the
full document, so chunk boundaries can never corrupt a span).
"""


def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """Split ``text`` into paragraph-aligned chunks of at most ``max_chars`` (best effort)."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        added = len(paragraph) + 2
        if current and current_len + added > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += added
    if current:
        chunks.append("\n\n".join(current))
    return [chunk for chunk in chunks if chunk.strip()]
