"""Extraction pipeline: snapshots -> chunks -> LLM -> provenance gate -> records.

Inputs: content-addressed snapshots under ``data/raw/``. Outputs: a list of
:class:`DocumentExtraction` (accepted AND rejected claims — rejections are
counted, never hidden). Failure mode: a document with no metadata/text pair is
skipped with nothing recorded; a claim that cannot be verified is recorded as
rejected (fail-closed, see ``reglens.provenance``).
"""

import json
from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

import httpx
import structlog
from pydantic import ValidationError

from reglens.config import Settings
from reglens.corpus import document_char_cap, in_extraction_sample
from reglens.extract.chunk import chunk_plan_sha256, chunk_text
from reglens.extract.llm import LLMProvider, input_sha256
from reglens.extract.records import ClaimRecord, DocumentExtraction, claim_id
from reglens.extract.schema import ExtractedObligation, RunMeta
from reglens.ingest.snapshot import iter_snapshots
from reglens.provenance import verify_span


class DocumentPair(NamedTuple):
    """A source document's metadata snapshot joined to its raw-text snapshot."""

    document_number: str
    title: str
    url: str
    text_sha256: str
    text: str
    publication_date: str = ""
    """ISO publication date from the source metadata; ``""`` when it carries none.

    Read by :func:`reglens.corpus.in_extraction_sample`, which is fail-closed on
    an absent or malformed value.
    """


def discover_documents(data_dir: Path) -> list[DocumentPair]:
    """Pair metadata and raw-text snapshots by document number, sorted for determinism."""
    metadata: dict[str, dict[str, str]] = {}
    texts: dict[str, tuple[str, str]] = {}
    for snapshot_dir, manifest in iter_snapshots(data_dir / "raw"):
        stem = Path(manifest.filename).stem
        payload = (snapshot_dir / manifest.filename).read_bytes()
        if manifest.content_type == "application/json":
            metadata[stem] = json.loads(payload)
        elif manifest.content_type == "text/plain":
            texts[stem] = (manifest.sha256, payload.decode())
    pairs: list[DocumentPair] = []
    for document_number in sorted(metadata.keys() & texts.keys()):
        meta = metadata[document_number]
        sha, text = texts[document_number]
        pairs.append(
            DocumentPair(
                document_number=document_number,
                title=str(meta.get("title", "")),
                url=str(meta.get("html_url", "")),
                text_sha256=sha,
                text=text,
                publication_date=str(meta.get("publication_date", "")),
            )
        )
    return pairs


def sampled_documents(pairs: Sequence[DocumentPair]) -> frozenset[str]:
    """The document numbers :func:`reglens.corpus.in_extraction_sample` selects."""
    return frozenset(
        pair.document_number
        for pair in pairs
        if in_extraction_sample(pair.document_number, pair.publication_date)
    )


def extract_obligations(
    provider: LLMProvider, chunks: list[str], *, workers: int = 1
) -> list[ExtractedObligation]:
    """Run the model over the given chunks and concatenate its proposals.

    Takes chunks rather than text so the caller owns chunking policy once: the
    sequence hashed into the run record is the same sequence that is sent to the
    model, not an equivalent one recomputed here.

    Chunks may be extracted concurrently (``workers`` > 1) but their results are
    always reassembled in chunk order, so the output does not depend on
    scheduling. Verified bit-identical to a serial run at temperature 0 with a
    pinned seed.

    Failure mode: a chunk whose model response is invalid or errors out yields
    NO obligations (fail-closed — logged, never guessed at); other chunks
    still process, so one bad response cannot sink a document.
    """
    logger = structlog.get_logger()

    def extract_chunk(indexed: tuple[int, str]) -> list[ExtractedObligation]:
        index, chunk = indexed
        try:
            return provider.extract(chunk).obligations
        except (ValidationError, httpx.HTTPError) as error:
            # Fail-closed: an unparseable or failed chunk contributes nothing.
            logger.warning("chunk-extraction-failed", chunk_index=index, error=type(error).__name__)
            return []

    if workers <= 1:
        per_chunk = [extract_chunk(item) for item in enumerate(chunks)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # pool.map preserves input order, so the concatenation stays deterministic.
            per_chunk = list(pool.map(extract_chunk, enumerate(chunks)))
    return [obligation for group in per_chunk for obligation in group]


def _bounded_text(text: str, max_chars: int | None) -> str:
    """Cap very long documents at a paragraph boundary; coverage is recorded, not hidden.

    ``max_chars=None`` means uncapped — see :func:`reglens.corpus.document_char_cap`
    for which documents that applies to and why.
    """
    if max_chars is None or len(text) <= max_chars:
        return text
    cut = text.rfind("\n\n", 0, max_chars)
    return text[: cut if cut > 0 else max_chars]


class DocumentPlan(NamedTuple):
    """Exactly what one run will send to the model: the bounded text, in chunks."""

    text: str
    chunks: list[str]


def document_plan(pair: DocumentPair, max_chars: int | None) -> DocumentPlan:
    """Resolve ``pair`` to the text and chunk sequence a run would use."""
    text = _bounded_text(pair.text, max_chars)
    return DocumentPlan(text=text, chunks=chunk_text(text))


def _plan_run_meta(provider: LLMProvider, plan: DocumentPlan) -> RunMeta:
    """The determinism record identifying a run of ``plan``."""
    return provider.run_meta(input_sha256(plan.text)).model_copy(
        update={"chunk_plan_sha256": chunk_plan_sha256(plan.chunks)}
    )


def document_run_meta(provider: LLMProvider, pair: DocumentPair, max_chars: int | None) -> RunMeta:
    """The determinism record a run of ``pair`` would produce, without calling the model.

    Shared by :func:`gate_document` and the reuse check so the two can never
    disagree about what identifies a run. The cap is folded in via the input
    hash and the chunk boundaries via the chunk-plan hash, so widening a
    document's cap OR changing the chunker invalidates its cached extraction.
    """
    return _plan_run_meta(provider, document_plan(pair, max_chars))


def gate_document(
    provider: LLMProvider, pair: DocumentPair, max_chars: int | None = 80_000, *, workers: int = 1
) -> DocumentExtraction:
    """Extract one document (bounded) and pass every claim through the provenance gate."""
    plan = document_plan(pair, max_chars)
    extraction_text = plan.text
    run_meta = _plan_run_meta(provider, plan)
    claims: list[ClaimRecord] = []
    seen: set[str] = set()
    for obligation in extract_obligations(provider, plan.chunks, workers=workers):
        identifier = claim_id(pair.text_sha256, obligation)
        if identifier in seen:
            continue  # identical span re-proposed by another chunk
        seen.add(identifier)
        verdict = verify_span(pair.text, obligation.quote)
        claims.append(
            ClaimRecord(
                claim_id=identifier,
                document_sha256=pair.text_sha256,
                document_number=pair.document_number,
                document_title=pair.title,
                document_url=pair.url,
                quote=obligation.quote,
                obligation_type=str(obligation.obligation_type),
                affected_party=obligation.affected_party,
                summary=obligation.summary,
                effective_date=obligation.effective_date,
                accepted=verdict.accepted,
                start=verdict.start,
                end=verdict.end,
                rejection_reason=verdict.reason,
                run=run_meta,
            )
        )
    accepted = sum(1 for claim in claims if claim.accepted)
    return DocumentExtraction(
        document_sha256=pair.text_sha256,
        document_number=pair.document_number,
        document_title=pair.title,
        document_url=pair.url,
        accepted_count=accepted,
        rejected_count=len(claims) - accepted,
        total_chars=len(pair.text),
        extracted_chars=len(extraction_text),
        run=run_meta,
        claims=claims,
    )


def _persist(processed_dir: Path, extractions: list[DocumentExtraction]) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    payload = [extraction.model_dump() for extraction in extractions]
    (processed_dir / "claims.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_persisted(processed_dir: Path) -> dict[str, DocumentExtraction]:
    """Previously extracted documents, keyed by source-text SHA-256.

    Failure mode: a missing or unparseable claims.json yields an empty mapping,
    so a corrupt checkpoint costs re-extraction rather than wrong results.
    """
    claims_path = processed_dir / "claims.json"
    if not claims_path.is_file():
        return {}
    try:
        payload = json.loads(claims_path.read_text())
        extractions = [DocumentExtraction.model_validate(item) for item in payload]
    except (json.JSONDecodeError, ValidationError):
        return {}
    return {extraction.document_sha256: extraction for extraction in extractions}


def reusable_extraction(
    persisted: dict[str, DocumentExtraction], pair: DocumentPair, expected_run: RunMeta
) -> DocumentExtraction | None:
    """A prior extraction of ``pair`` iff it is provably the same run, else None.

    Reuse requires the source SHA to match, the document's own run record to
    equal ``expected_run``, and every persisted claim to agree with it — so a
    changed model, prompt, runtime or chunk plan invalidates the cache
    automatically. Checking the document record as well as the claims is what
    lets a document that legitimately yielded NO claims be reused: its
    provenance is the run that read it, not the output of that run.

    Failure mode: fail-closed. A record predating the document-level run field
    carries ``None``, which never matches, so it is re-extracted rather than
    trusted.
    """
    previous = persisted.get(pair.text_sha256)
    if previous is None or previous.run != expected_run:
        return None
    if any(claim.run != expected_run for claim in previous.claims):
        return None
    return previous


def run_pipeline(
    settings: Settings,
    provider: LLMProvider,
    *,
    force: bool = False,
    documents: AbstractSet[str] | None = None,
) -> list[DocumentExtraction]:
    """Extract + gate the sampled documents; persist to data/processed/claims.json.

    Idempotent: a document whose source SHA, model tag, prompt hash, runtime and
    chunk plan already appear in claims.json is reused rather than re-inferred,
    so re-running over an unchanged corpus is a no-op and an interrupted run
    resumes where it stopped. ``force=True`` re-extracts the selected documents.
    Checkpoints after every document so a long run interrupted midway still
    leaves a valid, self-consistent claims.json on disk.

    ``documents`` restricts which documents this run may *infer*. It defaults to
    :func:`reglens.corpus.in_extraction_sample`, so a bare run covers the stated
    sample and never the whole corpus by surprise; pass every discovered document
    number to extract the corpus in full (hours of local inference).

    The two modes differ in what they do with documents they did not select, and
    the difference matters:

    * **Default (the sample).** The output IS the sample — anything outside it
      is dropped, not carried. Otherwise a previous wider run would leak into
      this one and the published ``documents_extracted`` would silently describe
      a corpus nobody asked for.
    * **Explicit ``documents``.** Targeted re-extraction. Everything else keeps
      its persisted extraction verbatim, including its original run record,
      which is never rewritten: a claim always reports the run that actually
      produced it. A document that is neither selected nor already persisted is
      dropped (fail-closed: no entry is better than an unprovenanced one).

    Every carry-forward and drop is logged.
    """
    logger = structlog.get_logger()
    processed_dir = settings.data_dir / "processed"
    persisted = load_persisted(processed_dir)
    reusable = {} if force else persisted
    extractions: list[DocumentExtraction] = []
    pairs = discover_documents(settings.data_dir)
    targeted = documents is not None
    selected = documents if documents is not None else sampled_documents(pairs)
    for pair in pairs:
        if pair.document_number not in selected:
            carried = persisted.get(pair.text_sha256) if targeted else None
            if carried is None:
                logger.info("document-skipped", document=pair.document_number)
                continue
            extractions.append(carried)
            logger.info("document-carried-forward", document=pair.document_number)
            continue
        cap = document_char_cap(pair.document_number, settings.max_document_chars)
        expected_run = document_run_meta(provider, pair, cap)
        cached = reusable_extraction(reusable, pair, expected_run)
        if cached is not None:
            extractions.append(cached)
            logger.info("document-reused", document=pair.document_number)
            continue
        extraction = gate_document(
            provider,
            pair,
            max_chars=cap,
            workers=settings.extract_workers,
        )
        extractions.append(extraction)
        _persist(processed_dir, extractions)
        logger.info(
            "document-extracted",
            document=pair.document_number,
            accepted=extraction.accepted_count,
            rejected=extraction.rejected_count,
        )
    _persist(processed_dir, extractions)
    return extractions
