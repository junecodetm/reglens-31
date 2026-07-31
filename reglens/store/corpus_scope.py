"""What was extracted, out of what is in scope — computed once, published everywhere.

Inputs: the raw snapshot tree and the persisted extractions. Output: a validated
:class:`reglens.api.schemas.Corpus`. Failure mode: pydantic ``ValidationError``
if a count is negative or missing; nothing is published on a partial record.

This exists as one function because the ratio it reports is a disclosure, and a
disclosure that is computed twice eventually disagrees with itself. The site's
``site.json`` and the static read API both render this object, so the numbers a
reviewer sees on the page are the same numbers the API serves, by construction.
"""

from collections.abc import Sequence

from reglens.api.schemas import Corpus
from reglens.config import Settings
from reglens.extract.records import DocumentExtraction
from reglens.extract.run import discover_documents


def build_corpus(
    settings: Settings, extractions: Sequence[DocumentExtraction], *, data_as_of: str
) -> Corpus:
    """Summarize extraction coverage against the full in-scope corpus.

    ``*_in_scope`` counts every document paired under ``data/raw`` — what is
    committed, which is the inclusion rule's output plus the documents an
    earlier citation-following pass reached that the CFR index does not tag (see
    docs/DATA_SOURCES.md). It is deliberately the committed set rather than the
    rule's output alone: the honest denominator for "how much was read" is
    everything available to read. ``*_extracted`` counts only what the local
    model was actually run over (:func:`reglens.corpus.in_extraction_sample`).
    Characters in scope are full source lengths, so the denominator is the text
    that exists, not the text that was selected for reading.

    The per-document cap travels with the counts rather than being restated by
    each consumer: the site quotes it in the same sentence as the character
    totals, and a cap the UI hard-coded could silently disagree with the one
    extraction actually applied.
    """
    pairs = discover_documents(settings.data_dir)
    return Corpus(
        data_as_of=data_as_of,
        max_document_chars=settings.max_document_chars,
        documents_extracted=len(extractions),
        documents_in_scope=len(pairs),
        chars_extracted=sum(extraction.extracted_chars for extraction in extractions),
        chars_in_scope=sum(len(pair.text) for pair in pairs),
        accepted_count=sum(extraction.accepted_count for extraction in extractions),
        rejected_count=sum(extraction.rejected_count for extraction in extractions),
        model_tags=sorted(
            {claim.run.model_tag for extraction in extractions for claim in extraction.claims}
        ),
    )
