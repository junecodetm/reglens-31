"""Pipeline: a real quote survives the gate with offsets; a fabricated one is counted rejected."""

from pathlib import Path

from reglens.config import Settings
from reglens.extract.run import discover_documents, gate_document, run_pipeline
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


def test_zero_claim_document_is_never_reused(tmp_path: Path) -> None:
    """Fail-closed: an empty result has no run record, so its provenance is unverifiable."""
    _seed_snapshots(tmp_path)
    settings = Settings(data_dir=tmp_path)
    run_pipeline(settings, EmptyProvider())

    second = EmptyProvider()
    run_pipeline(settings, second)
    assert second.calls > 0
