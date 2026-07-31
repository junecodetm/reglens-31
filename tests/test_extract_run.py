"""Pipeline: a real quote survives the gate with offsets; a fabricated one is counted rejected."""

import json
import time
from pathlib import Path

import pytest

from reglens.config import Settings
from reglens.extract import run as run_module
from reglens.extract.chunk import chunk_text
from reglens.extract.run import (
    discover_documents,
    extract_obligations,
    gate_document,
    run_pipeline,
)
from reglens.extract.schema import (
    ExtractedObligation,
    ExtractionResult,
    ObligationType,
    RunMeta,
)
from reglens.ingest.snapshot import write_snapshot

SOURCE_TEXT = (
    "PART 1010 -- GENERAL PROVISIONS\n\n"
    "Each financial institution must file a report within 30 days of the transaction.\n\n"
    "Records must be retained for five years."
)

REAL_QUOTE = "Each financial institution must file a report within 30 days"
FABRICATED_QUOTE = "Each broker must notify the Secretary immediately."


class FakeProvider:
    """Deterministic stand-in for the local model: one real span, one fabricated."""

    def extract(self, document_text: str) -> ExtractionResult:
        return ExtractionResult(
            obligations=[
                ExtractedObligation(
                    quote=REAL_QUOTE,
                    obligation_type=ObligationType.REPORTING,
                    affected_party="financial institutions",
                    summary="File a report within 30 days.",
                    effective_date=None,
                ),
                ExtractedObligation(
                    quote=FABRICATED_QUOTE,
                    obligation_type=ObligationType.REQUIREMENT,
                    affected_party="brokers",
                    summary="Fabricated claim that must be rejected.",
                    effective_date=None,
                ),
            ]
        )

    def run_meta(self, input_sha256: str) -> RunMeta:
        return RunMeta(model_tag="fake", prompt_sha256="0" * 64, input_sha256=input_sha256)


def _seed_snapshots(tmp_path: Path) -> None:
    write_snapshot(
        tmp_path,
        source_id="federal_register",
        url="https://www.federalregister.gov/api/v1/documents/2026-00001.json",
        content=(
            b'{"document_number": "2026-00001", "title": "Test Rule",'
            b' "publication_date": "2026-01-02",'
            b' "html_url": "https://www.federalregister.gov/documents/2026-00001"}'
        ),
        content_type="application/json",
        filename="2026-00001.json",
    )
    write_snapshot(
        tmp_path,
        source_id="federal_register",
        url="https://www.federalregister.gov/documents/full_text/text/2026-00001.txt",
        content=SOURCE_TEXT.encode(),
        content_type="text/plain",
        filename="2026-00001.txt",
    )


def test_pipeline_accepts_real_and_rejects_fabricated(tmp_path: Path) -> None:
    _seed_snapshots(tmp_path)
    pairs = discover_documents(tmp_path)
    assert len(pairs) == 1

    extraction = gate_document(FakeProvider(), pairs[0])
    assert extraction.accepted_count == 1
    assert extraction.rejected_count == 1

    accepted = next(claim for claim in extraction.claims if claim.accepted)
    assert accepted.start is not None and accepted.end is not None
    assert SOURCE_TEXT[accepted.start : accepted.end] == REAL_QUOTE

    rejected = next(claim for claim in extraction.claims if not claim.accepted)
    assert rejected.quote == FABRICATED_QUOTE
    assert rejected.rejection_reason == "not-a-substring"


def test_run_pipeline_writes_claims_json(tmp_path: Path) -> None:
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    extractions = run_pipeline(settings, FakeProvider())
    assert len(extractions) == 1
    assert (tmp_path / "processed" / "claims.json").is_file()


class OrderedProvider:
    """Returns one obligation naming its chunk, with a jittered delay per chunk.

    The delay is inversely proportional to the chunk's position, so later chunks
    finish FIRST under concurrency — any implementation that appends results as
    they complete produces the wrong order and fails the test.
    """

    def __init__(self, chunk_count: int) -> None:
        self._chunk_count = chunk_count

    def extract(self, document_text: str) -> ExtractionResult:
        marker = document_text.strip().split(" ", maxsplit=1)[0]
        time.sleep(0.02 * (self._chunk_count - int(marker.split("-")[1])))
        return ExtractionResult(
            obligations=[
                ExtractedObligation(
                    quote=marker,
                    obligation_type=ObligationType.REQUIREMENT,
                    affected_party="party",
                    summary=f"From {marker}.",
                    effective_date=None,
                )
            ]
        )

    def run_meta(self, input_sha256: str) -> RunMeta:
        return RunMeta(model_tag="ordered", prompt_sha256="0" * 64, input_sha256=input_sha256)


def test_concurrent_extraction_preserves_chunk_order() -> None:
    """Determinism: output must not depend on which chunk finishes first."""
    chunk_count = 6
    # Each paragraph fits chunk_text's 4000-char budget but two never do, so
    # every paragraph becomes exactly one chunk.
    text = "\n\n".join(f"chunk-{index} " + "x" * 3000 for index in range(chunk_count))
    chunks = chunk_text(text)
    assert len(chunks) == chunk_count
    provider = OrderedProvider(chunk_count)

    serial = extract_obligations(provider, chunks, workers=1)
    concurrent = extract_obligations(provider, chunks, workers=chunk_count)

    assert [o.quote for o in serial] == [o.quote for o in concurrent]
    assert [o.quote for o in concurrent] == [f"chunk-{i}" for i in range(chunk_count)]


class CountingProvider(FakeProvider):
    """FakeProvider that records how many times the model was actually called."""

    def __init__(self, model_tag: str = "fake") -> None:
        self.calls = 0
        self._model_tag = model_tag

    def extract(self, document_text: str) -> ExtractionResult:
        self.calls += 1
        return super().extract(document_text)

    def run_meta(self, input_sha256: str) -> RunMeta:
        return RunMeta(model_tag=self._model_tag, prompt_sha256="0" * 64, input_sha256=input_sha256)


def test_rerun_over_unchanged_corpus_is_a_no_op(tmp_path: Path) -> None:
    """The idempotency claim in docs/ARCHITECTURE.md: same input SHA, no re-inference."""
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    claims_path = tmp_path / "processed" / "claims.json"

    first = CountingProvider()
    run_pipeline(settings, first)
    assert first.calls > 0
    after_first = claims_path.read_text()

    second = CountingProvider()
    run_pipeline(settings, second)
    assert second.calls == 0, "unchanged document must not be re-inferred"
    assert claims_path.read_text() == after_first, "reuse must be byte-identical"


def test_force_re_extracts(tmp_path: Path) -> None:
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, CountingProvider())

    forced = CountingProvider()
    run_pipeline(settings, forced, force=True)
    assert forced.calls > 0


def test_changed_model_tag_invalidates_the_cache(tmp_path: Path) -> None:
    """A different model must never silently reuse another model's claims."""
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, CountingProvider(model_tag="fake"))

    other = CountingProvider(model_tag="other-model")
    run_pipeline(settings, other)
    assert other.calls > 0


class EmptyProvider(FakeProvider):
    """Yields no obligations, so the persisted document carries no run record."""

    def __init__(self) -> None:
        self.calls = 0

    def extract(self, document_text: str) -> ExtractionResult:
        self.calls += 1
        return ExtractionResult(obligations=[])


def test_a_changed_chunk_plan_invalidates_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The model reads one chunk at a time, so different boundaries are a different run.

    This is the defect the chunk-plan hash exists to catch: before it, replacing
    the chunker left the reuse key unchanged and stale claims were kept silently.
    """
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, CountingProvider())

    def finer_chunks(text: str, max_chars: int = 4000) -> list[str]:
        return chunk_text(text, max_chars=40)

    monkeypatch.setattr(run_module, "chunk_text", finer_chunks)
    rechunked = CountingProvider()
    run_pipeline(settings, rechunked)

    assert rechunked.calls > 0, "a re-chunked document must be re-extracted, not reused"


def test_a_record_predating_the_chunk_plan_field_is_never_reused(tmp_path: Path) -> None:
    """Fail-closed on legacy provenance: 'unknown' can never match a computed plan."""
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, CountingProvider())

    claims_path = tmp_path / "processed" / "claims.json"
    payload = json.loads(claims_path.read_text())
    for document in payload:
        for claim in document["claims"]:
            claim["run"]["chunk_plan_sha256"] = "unknown"
    claims_path.write_text(json.dumps(payload))

    legacy = CountingProvider()
    run_pipeline(settings, legacy)
    assert legacy.calls > 0


def test_a_document_that_yields_no_claims_is_still_reused(tmp_path: Path) -> None:
    """Idempotency held for every document except the empty ones, until it didn't.

    A document the model read and found nothing in has a real run record — the
    run that read it. Without a document-level record it looked identical to a
    document never processed, so it was re-inferred on every pass and the
    published no-op guarantee was false for it.
    """
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, EmptyProvider())

    second = EmptyProvider()
    run_pipeline(settings, second)
    assert second.calls == 0, "a zero-claim document must not be re-inferred"


def test_a_zero_claim_record_without_provenance_is_not_reused(tmp_path: Path) -> None:
    """Fail-closed: a record predating the document-level run field is re-extracted."""
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, EmptyProvider())

    claims_path = tmp_path / "processed" / "claims.json"
    payload = json.loads(claims_path.read_text())
    for document in payload:
        document["run"] = None
    claims_path.write_text(json.dumps(payload))

    legacy = EmptyProvider()
    run_pipeline(settings, legacy)
    assert legacy.calls > 0


def test_a_second_run_leaves_claims_json_byte_identical(tmp_path: Path) -> None:
    """The replay claim, checked on the artifact rather than on the call count."""
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    claims_path = tmp_path / "processed" / "claims.json"

    run_pipeline(settings, FakeProvider())
    first = claims_path.read_bytes()
    run_pipeline(settings, FakeProvider())

    assert claims_path.read_bytes() == first


def test_documents_outside_the_sample_are_neither_inferred_nor_invented(tmp_path: Path) -> None:
    """The sample rule bounds the run; an unsampled document yields no unprovenanced entry."""
    _seed_snapshots(tmp_path)
    write_snapshot(
        tmp_path,
        source_id="federal_register",
        url="https://www.federalregister.gov/api/v1/documents/2019-00002.json",
        content=(
            b'{"document_number": "2019-00002", "title": "Older Rule",'
            b' "publication_date": "2019-05-06",'
            b' "html_url": "https://www.federalregister.gov/documents/2019-00002"}'
        ),
        content_type="application/json",
        filename="2019-00002.json",
    )
    write_snapshot(
        tmp_path,
        source_id="federal_register",
        # Snapshots are content-addressed, so the second document needs its own text.
        url="https://www.federalregister.gov/documents/full_text/text/2019-00002.txt",
        content=(SOURCE_TEXT + "\n\nBanks must retain these records.").encode(),
        content_type="text/plain",
        filename="2019-00002.txt",
    )
    settings = Settings(data_dir=tmp_path)

    assert len(discover_documents(tmp_path)) == 2
    extractions = run_pipeline(settings, FakeProvider())

    assert [extraction.document_number for extraction in extractions] == ["2026-00001"]

    # --all widens the run to the whole corpus.
    every = {pair.document_number for pair in discover_documents(tmp_path)}
    widened = run_pipeline(settings, FakeProvider(), documents=every)
    assert {extraction.document_number for extraction in widened} == every

    # ...and a later default run narrows straight back to the sample. Carrying
    # the wider result forward would make the published documents_extracted
    # describe a corpus the stated rule does not select.
    narrowed = run_pipeline(settings, FakeProvider())
    assert [extraction.document_number for extraction in narrowed] == ["2026-00001"]


def test_targeted_reextraction_carries_other_documents_forward(tmp_path: Path) -> None:
    """`--documents` is surgical: it must not discard work it did not select."""
    _seed_snapshots(tmp_path)
    write_snapshot(
        tmp_path,
        source_id="federal_register",
        url="https://www.federalregister.gov/api/v1/documents/2026-00003.json",
        content=(
            b'{"document_number": "2026-00003", "title": "Second Rule",'
            b' "publication_date": "2026-03-04",'
            b' "html_url": "https://www.federalregister.gov/documents/2026-00003"}'
        ),
        content_type="application/json",
        filename="2026-00003.json",
    )
    write_snapshot(
        tmp_path,
        source_id="federal_register",
        url="https://www.federalregister.gov/documents/full_text/text/2026-00003.txt",
        content=(SOURCE_TEXT + "\n\nBanks must retain these records.").encode(),
        content_type="text/plain",
        filename="2026-00003.txt",
    )
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, FakeProvider())

    targeted = CountingProvider()
    extractions = run_pipeline(settings, targeted, force=True, documents={"2026-00001"})

    assert {extraction.document_number for extraction in extractions} == {
        "2026-00001",
        "2026-00003",
    }
    assert targeted.calls > 0
