"""The published coverage ratio is derived from the corpus, and it is honest.

The site's headline disclosure is that extraction covers a stated sample of a
larger committed corpus. That claim is only worth anything if the numbers behind
it come from counting the corpus rather than from being typed somewhere, so
these tests re-derive them and hold the published artifact to the result.
"""

import json
from pathlib import Path

from reglens.api.schemas import Corpus
from reglens.config import Settings
from reglens.corpus import document_char_cap
from reglens.extract.records import load_extractions
from reglens.extract.run import discover_documents
from reglens.store.corpus_scope import build_corpus

DATA_DIR = Path("data")
SITE_JSON = Path("web") / "public" / "data" / "site.json"
WEB_CLAIMS = Path("web") / "public" / "data" / "claims.json"


def _built() -> Corpus:
    settings = Settings(data_dir=DATA_DIR)
    extractions = load_extractions(DATA_DIR / "processed" / "claims.json")
    return build_corpus(settings, extractions, data_as_of="2026-07-30")


def test_extraction_covers_a_strict_subset_of_the_committed_corpus() -> None:
    corpus = _built()

    assert 0 < corpus.documents_extracted < corpus.documents_in_scope
    assert 0 < corpus.chars_extracted <= corpus.chars_in_scope


def test_in_scope_counts_come_from_the_snapshots_themselves() -> None:
    """Not a stored number: the denominator is whatever is committed under data/raw."""
    pairs = discover_documents(DATA_DIR)
    corpus = _built()

    assert corpus.documents_in_scope == len(pairs)
    assert corpus.chars_in_scope == sum(len(pair.text) for pair in pairs)


def test_the_published_cap_is_the_cap_extraction_applied() -> None:
    """The UI quotes this number; a hand-typed copy of it could silently diverge."""
    assert _built().max_document_chars == Settings().max_document_chars


def test_the_published_site_metadata_matches_what_the_site_renders() -> None:
    """site.json must agree with the claims file beside it, field for field."""
    site = Corpus.model_validate(json.loads(SITE_JSON.read_text()))
    documents = json.loads(WEB_CLAIMS.read_text())

    assert site.documents_extracted == len(documents)
    assert site.accepted_count == sum(document["accepted_count"] for document in documents)
    assert site.rejected_count == sum(document["rejected_count"] for document in documents)
    assert site.chars_extracted == sum(document["extracted_chars"] for document in documents)
    assert site.model_tags


def test_the_part_texts_are_extracted_uncapped() -> None:
    """The corrected policy: the standing law is read in full, not to a cap.

    Asserted against the rule rather than the artifact, so it holds at every
    commit. The artifact-level check — that every part's ``extracted_chars``
    equals its ``total_chars`` — lands with the re-extraction that satisfies it.
    """
    documents = json.loads(WEB_CLAIMS.read_text())
    parts = [
        document for document in documents if document["document_number"].startswith("31-CFR-")
    ]

    assert parts, "the CFR part texts must be part of the extracted sample"
    for part in parts:
        assert document_char_cap(part["document_number"], 80_000) is None


def test_the_part_texts_are_reported_as_fully_read() -> None:
    """The silent-truncation defect this pass fixed would show up here as a shortfall."""
    documents = json.loads(WEB_CLAIMS.read_text())
    parts = [
        document for document in documents if document["document_number"].startswith("31-CFR-")
    ]
    assert parts
    for part in parts:
        assert part["extracted_chars"] == part["total_chars"], part["document_number"]
