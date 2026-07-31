"""The two corpus rules select what they claim to, against the committed snapshots.

Scope is stated twice in this project — what is ingested, and what extraction
covers — and a rule nobody checks is just a comment. These tests hold both to
the real ``data/raw`` tree, so a sample that quietly drifted away from its
stated rule fails here rather than being discovered by a reader of the site.
"""

from pathlib import Path

from reglens.corpus import (
    CFR_PARTS,
    EXTRACTION_YEAR,
    PART_DOCUMENT_NUMBERS,
    document_char_cap,
    in_extraction_sample,
)
from reglens.extract.records import load_extractions
from reglens.extract.run import discover_documents, sampled_documents

DATA_DIR = Path("data")

# Pinned so a change to the sample is a deliberate edit here, not a silent
# consequence of ingesting more documents.
EXPECTED_SAMPLE_SIZE = 25
EXPECTED_IN_SCOPE_SIZE = 157


def test_the_extraction_sample_is_the_five_parts_plus_one_publication_year() -> None:
    sample = sampled_documents(discover_documents(DATA_DIR))

    assert sample >= PART_DOCUMENT_NUMBERS
    federal_register = sample - PART_DOCUMENT_NUMBERS
    assert federal_register, "the sample must contain rulemaking, not only the part texts"
    assert len(sample) == EXPECTED_SAMPLE_SIZE


def test_the_sample_is_a_strict_subset_of_what_is_ingested() -> None:
    """The point of the disclosure: everything in scope is committed, some is extracted."""
    pairs = discover_documents(DATA_DIR)

    assert len(pairs) == EXPECTED_IN_SCOPE_SIZE
    assert sampled_documents(pairs) < {pair.document_number for pair in pairs}


def test_every_extracted_document_is_one_the_rule_selects() -> None:
    """No document may appear in the published claims that the stated rule excludes."""
    extracted = {
        extraction.document_number
        for extraction in load_extractions(DATA_DIR / "processed" / "claims.json")
    }

    assert extracted == sampled_documents(discover_documents(DATA_DIR))


def test_a_document_from_another_year_is_excluded() -> None:
    assert in_extraction_sample("2026-00001", f"{EXTRACTION_YEAR}-01-02")
    assert not in_extraction_sample("2019-00001", f"{EXTRACTION_YEAR - 7}-01-02")


def test_an_undated_federal_register_document_is_excluded_fail_closed() -> None:
    """A document that cannot be placed in a year cannot be shown to satisfy the rule."""
    assert not in_extraction_sample("2026-00001", "")
    assert not in_extraction_sample("2026-00001", "2026")
    assert not in_extraction_sample("2026-00001", "not-a-date")


def test_a_part_text_is_sampled_regardless_of_publication_date() -> None:
    """Part texts are the standing law, not rulemaking; they carry no publication date."""
    for part_document in PART_DOCUMENT_NUMBERS:
        assert in_extraction_sample(part_document, "")


def test_only_the_part_texts_are_extracted_uncapped() -> None:
    assert len(PART_DOCUMENT_NUMBERS) == len(CFR_PARTS)
    for part_document in PART_DOCUMENT_NUMBERS:
        assert document_char_cap(part_document, 80_000) is None
    assert document_char_cap("2026-00001", 80_000) == 80_000
