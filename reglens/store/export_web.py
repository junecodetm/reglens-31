"""Export processed records and source texts as static assets for the web UI.

Inputs: ``data/processed/claims.json`` and the raw snapshots it references.
Outputs: ``web/public/data/claims.json``, ``web/public/data/documents/<n>.txt``
and ``web/public/data/site.json`` plus the OGC01 authority assets, CFR section
structure, and lexical search index. Counts, model tags, and "as of" dates come
from persisted inputs, never wall-clock time. Failure mode: missing inputs raise
``FileNotFoundError``; malformed records raise ``ValidationError``; parts with
no sections and search indexes larger than 4 MiB raise ``ValueError``.
"""

import difflib
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

from reglens.authority.records import AuthorityExport
from reglens.config import Settings
from reglens.extract.records import ClaimRecord, DocumentExtraction, load_extractions
from reglens.ingest.federal_register import require_safe_document_number
from reglens.ingest.snapshot import iter_snapshots, read_manifest
from reglens.provenance import normalize, normalize_with_map
from reglens.search_index import (
    CfrSectionRef,
    SearchSource,
    build_search_index,
    serialize_search_index,
)
from reglens.structure import (
    PartStructure,
    SectionsExport,
    build_sections_export,
    split_part_text,
)
from reglens.use_case_inventory import UseCaseInventoryExport, parse_inventory_csv

_USC_TEXT_FILENAME = re.compile(r"usc-(?P<title>\d+)-s(?P<section>[A-Za-z0-9]+)\.txt")

# Pinned content address of the committed Treasury AI Use Case Inventory CSV
# snapshot (reglens.ingest.inventory). A re-snapshot that changes the file
# must update this pin deliberately; the exporter refuses any other bytes.
INVENTORY_SNAPSHOT_SHA256 = "8e3f3332f26af5de23c2c0dda4c8e41f0ceb9097edcbd169e1216e0e6cf7512f"

# Pinned document categories for the UI document picker. Every exported
# document number MUST appear here; a new corpus document requires a
# deliberate pin (fail-closed, like INVENTORY_SNAPSHOT_SHA256).
CATEGORY_ORDER = (
    "Title 31 — Code of Federal Regulations parts",
    "Sanctions notices & general licenses (OFAC)",
    "IRS & tax regulations",
    "Other Treasury & joint-agency rules",
)
DOC_CATEGORIES: dict[str, str] = {
    "31-CFR-50": CATEGORY_ORDER[0],
    "31-CFR-223": CATEGORY_ORDER[0],
    "31-CFR-285": CATEGORY_ORDER[0],
    "31-CFR-356": CATEGORY_ORDER[0],
    "31-CFR-501": CATEGORY_ORDER[0],
    "2026-09090": CATEGORY_ORDER[1],
    "2026-09092": CATEGORY_ORDER[1],
    "2026-09094": CATEGORY_ORDER[1],
    "2026-11592": CATEGORY_ORDER[1],
    "2026-11601": CATEGORY_ORDER[1],
    "2026-11614": CATEGORY_ORDER[1],
    "2026-11615": CATEGORY_ORDER[1],
    "2026-11616": CATEGORY_ORDER[1],
    "2026-11761": CATEGORY_ORDER[1],
    "2026-15112": CATEGORY_ORDER[1],
    "2026-10116": CATEGORY_ORDER[2],
    "2026-13830": CATEGORY_ORDER[2],
    "2026-13851": CATEGORY_ORDER[2],
    "2026-13925": CATEGORY_ORDER[2],
    "2026-15008": CATEGORY_ORDER[2],
    "2026-10036": CATEGORY_ORDER[3],
    "C1-2026-10036": CATEGORY_ORDER[3],
    "2026-10037": CATEGORY_ORDER[3],
    "2026-11140": CATEGORY_ORDER[3],
    "2026-12787": CATEGORY_ORDER[3],
}
EXAMPLE_ACCEPTED_CLAIM_ID = "fe677d4f490f99b2"
EXAMPLE_REJECTED_CLAIM_ID = "33961b9a82254639"


class _NoClosestDetail(TypedDict):
    """Comparison result when no sufficiently similar source passage exists."""

    similarity: float
    closest: None


class _ClosestDetail(TypedDict):
    """Comparison result with a word-aligned source passage and word-level diff."""

    similarity: float
    closest_start: int
    closest_end: int
    closest_quote: str
    diff: list[list[str]]


type _RejectedDetail = _NoClosestDetail | _ClosestDetail


class _RejectedDetailsPayload(TypedDict):
    """Serialized shape of ``rejected-details.json``."""

    schema_version: int
    method: str
    details: dict[str, _RejectedDetail]


class _AcceptedExamplePayload(TypedDict):
    """Serialized accepted side of the provenance-gate example."""

    claim_id: str
    document_number: str
    document_title: str
    summary: str
    quote: str
    excerpt: str
    span_start: int
    span_end: int


class _ExamplePayload(TypedDict):
    """Serialized shape of ``example.json``."""

    accepted: _AcceptedExamplePayload
    rejected: dict[str, object]


def _snapshot_payload_path(snapshot_dir: Path, filename: str) -> Path:
    """Resolve a manifest payload filename without allowing directory escape.

    Inputs:
        snapshot_dir: Content-addressed directory that owns the payload.
        filename: Untrusted filename read from the snapshot manifest.

    Returns:
        The payload path directly beneath ``snapshot_dir``.

    Raises:
        ValueError: If ``filename`` is empty, absolute, or contains a directory.
    """
    candidate = Path(filename)
    if not filename or filename in {".", ".."} or candidate.name != filename:
        raise ValueError(f"Unsafe snapshot filename: {filename!r}")
    return snapshot_dir / candidate


# Public alias for tests (repo pattern: tests never import private names).
snapshot_payload_path = _snapshot_payload_path


def _sanitized(extraction: DocumentExtraction) -> DocumentExtraction:
    """Enforce https on the outbound link; refuse unsafe document numbers."""
    require_safe_document_number(extraction.document_number)
    if extraction.document_url.startswith("https://"):
        return extraction
    claims = [claim.model_copy(update={"document_url": ""}) for claim in extraction.claims]
    return extraction.model_copy(update={"document_url": "", "claims": claims})


def _claim_search_sources(
    extractions: Sequence[DocumentExtraction],
) -> list[SearchSource]:
    """Build deterministic search sources for accepted claim summaries.

    Inputs:
        extractions: Validated records from the already-exported claims payload.

    Returns:
        Accepted claims sorted by document identifier and claim identifier.

    Failure mode:
        Pydantic ``ValidationError`` propagates if generated source metadata is invalid.
    """
    claims = sorted(
        (claim for extraction in extractions for claim in extraction.claims if claim.accepted),
        key=lambda claim: (claim.document_number, claim.claim_id),
    )
    return [
        SearchSource(
            id=f"claim:{claim.claim_id}",
            type="claim",
            label=claim.summary,
            ref=claim.document_number,
            text=claim.summary,
        )
        for claim in claims
    ]


def _resolved_usc_headings(
    export: AuthorityExport,
) -> dict[tuple[int, str], str | None]:
    """Collect one consistent optional heading for every resolved U.S.C. section.

    Inputs:
        export: Validated authority records that supplied the exported U.S.C. texts.

    Returns:
        A mapping from ``(title, section)`` to the recorded heading or ``None``.

    Raises:
        ValueError: If duplicate resolved records disagree about a section heading.
    """
    headings: dict[tuple[int, str], str | None] = {}
    for part in export.parts:
        for resolved in part.resolved:
            key = (resolved.usc_title, resolved.usc_section)
            if key in headings and headings[key] != resolved.heading:
                raise ValueError(f"Conflicting U.S.C. headings for {key[0]} U.S.C. {key[1]}")
            headings[key] = resolved.heading
    return headings


def _usc_search_sources(
    usc_dir: Path,
    headings: Mapping[tuple[int, str], str | None],
) -> list[SearchSource]:
    """Build deterministic search sources from every exported U.S.C. text.

    Inputs:
        usc_dir: Directory containing exported ``usc-<title>-s<section>.txt`` files.
        headings: Optional authoritative headings keyed by U.S.C. title and section.

    Returns:
        Sources sorted by exact filename with ``usc/<filename>`` references.

    Raises:
        ValueError: If an exported text filename does not match the required convention.
        UnicodeError: If an exported text is not valid UTF-8.
    """
    sources: list[SearchSource] = []
    for path in sorted(usc_dir.glob("*.txt"), key=lambda candidate: candidate.name):
        match = _USC_TEXT_FILENAME.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Unexpected exported U.S.C. filename: {path.name}")
        title = int(match.group("title"))
        section = match.group("section")
        label = f"{title} U.S.C. § {section}"
        heading = headings.get((title, section))
        if heading:
            label = f"{label} — {heading}"
        sources.append(
            SearchSource(
                id=f"usc:{path.name}",
                type="usc",
                label=label,
                ref=f"usc/{path.name}",
                text=path.read_text(encoding="utf-8"),
            )
        )
    return sources


def _cfr_search_sources(
    sections: SectionsExport,
    out_dir: Path,
) -> list[SearchSource]:
    """Build deterministic search sources from exact exported CFR section slices.

    Inputs:
        sections: Validated part structure with offsets into published text files.
        out_dir: Static data directory containing every ``text_path``.

    Returns:
        CFR sources ordered by part and source offset.

    Raises:
        FileNotFoundError: If a referenced part text is absent.
        ValueError: If an offset lies outside its text or misses its designation.
        UnicodeError: If an exported text is not valid UTF-8.
    """
    sources: list[SearchSource] = []
    for part in sorted(sections.parts, key=lambda item: item.part):
        text = (out_dir / part.text_path).read_text(encoding="utf-8")
        for section in sorted(part.sections, key=lambda item: item.start):
            if section.end > len(text) or not text[section.start :].startswith(section.designation):
                raise ValueError(
                    f"Invalid CFR section offsets for part {part.part}: "
                    f"{section.designation} [{section.start}, {section.end})"
                )
            section_text = text[section.start : section.end]
            section_key = section.designation.lstrip("§").strip().replace(" ", "")
            sources.append(
                SearchSource(
                    id=f"cfr:{sections.title}:{section_key}",
                    type="cfr-section",
                    label=(f"{sections.title} CFR {section.designation} {section.heading}"),
                    ref=CfrSectionRef(
                        part=part.part,
                        start=section.start,
                        end=section.end,
                    ),
                    text=section_text,
                )
            )
    return sources


def _draft_search_sources(drafts_dir: Path) -> list[SearchSource]:
    """Build deterministic search sources from every accepted exported draft.

    Inputs:
        drafts_dir: Directory containing the accepted draft text files.

    Returns:
        Whole-draft sources sorted by exact filename.

    Failure mode:
        ``UnicodeError`` propagates if an exported draft is not valid UTF-8.
    """
    return [
        SearchSource(
            id=f"draft:{path.name}",
            type="draft",
            label=path.name,
            ref=path.name,
            text=path.read_text(encoding="utf-8"),
        )
        for path in sorted(drafts_dir.glob("*.txt"), key=lambda candidate: candidate.name)
    ]


def _derive_sections(export: AuthorityExport, out_dir: Path) -> SectionsExport:
    """Split every authority part against its exact exported text.

    Inputs:
        export: Validated authority records carrying title, part, and part headings.
        out_dir: Static data directory containing ``authority-parts``.

    Returns:
        A title-level section export ordered by part number.

    Raises:
        FileNotFoundError: If an expected exported part text is absent.
        ValueError: If titles conflict, text hashes differ, or a part yields no sections.
    """
    titles = {part.cfr_title for part in export.parts}
    if len(titles) != 1:
        raise ValueError(f"Authority export must contain exactly one CFR title, got {titles}")
    title = next(iter(titles))
    parts: list[PartStructure] = []
    for part in sorted(export.parts, key=lambda item: item.part):
        filename = f"{part.cfr_title}-CFR-{part.part}.txt"
        text_path = f"authority-parts/{filename}"
        text = (out_dir / text_path).read_text(encoding="utf-8")
        actual_sha256 = hashlib.sha256(text.encode()).hexdigest()
        if actual_sha256 != part.part_text_sha256:
            raise ValueError(
                f"Exported part text hash mismatch for {part.cfr_title} CFR part {part.part}"
            )
        parts.append(
            split_part_text(
                part=part.part,
                heading=part.part_heading,
                text_path=text_path,
                text=text,
            )
        )
    return build_sections_export(title=title, parts=parts)


def _export_structure_and_search(export: AuthorityExport, out_dir: Path) -> None:
    """Write CFR structure and lexical index after fully validating both payloads.

    Inputs:
        export: Validated authority records already written to ``authority.json``.
        out_dir: Static data directory containing claims, U.S.C., CFR, and draft texts.

    Outputs:
        ``sections.json`` and ``search-index.json`` in ``out_dir``.

    Failure mode:
        Missing/malformed inputs, unsplittable parts, invalid offsets, and an index over
        4 MiB raise before either new artifact is written.
    """
    sections = _derive_sections(export, out_dir)
    extractions = load_extractions(out_dir / "claims.json")
    sources = [
        *_claim_search_sources(extractions),
        *_usc_search_sources(out_dir / "usc", _resolved_usc_headings(export)),
        *_cfr_search_sources(sections, out_dir),
        *_draft_search_sources(out_dir / "drafts"),
    ]
    sections_json = (
        json.dumps(
            sections.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    search_json = serialize_search_index(build_search_index(sources))
    (out_dir / "sections.json").write_text(sections_json, encoding="utf-8", newline="\n")
    (out_dir / "search-index.json").write_text(search_json, encoding="utf-8", newline="\n")


def export_web_data(settings: Settings, web_dir: Path) -> Path:
    """Copy claims, per-document text, and site metadata into ``web/public/data``.

    Inputs:
        settings: Repository data paths containing processed claims and raw snapshots.
        web_dir: Web project root whose ``public/data`` directory receives the export.

    Returns:
        The populated static-data directory.

    Failure mode:
        Missing or malformed inputs propagate; an unpinned document category raises
        ``ValueError`` before ``claims.json`` is written.
    """
    claims_path = settings.data_dir / "processed" / "claims.json"
    extractions = [_sanitized(extraction) for extraction in load_extractions(claims_path)]

    out_dir = web_dir / "public" / "data"
    documents_dir = out_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    by_sha = {extraction.document_sha256: extraction for extraction in extractions}
    latest_fetch = ""
    for snapshot_dir, manifest in iter_snapshots(settings.data_dir / "raw"):
        latest_fetch = max(latest_fetch, manifest.fetched_at)
        extraction = by_sha.get(manifest.sha256)
        if manifest.content_type == "text/plain" and extraction is not None:
            source = _snapshot_payload_path(snapshot_dir, manifest.filename).read_text()
            (documents_dir / f"{extraction.document_number}.txt").write_text(
                source, encoding="utf-8", newline="\n"
            )

    model_tags = sorted(
        {claim.run.model_tag for extraction in extractions for claim in extraction.claims}
    )
    accepted = sum(extraction.accepted_count for extraction in extractions)
    rejected = sum(extraction.rejected_count for extraction in extractions)
    payload = [extraction.model_dump() for extraction in extractions]
    for extraction, document in zip(extractions, payload, strict=True):
        n = extraction.document_number
        category = DOC_CATEGORIES.get(n)
        if category is None:
            raise ValueError(f"Document {n!r} has no pinned category")
        document["category"] = category
    (out_dir / "claims.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    site = {
        "accepted_count": accepted,
        "rejected_count": rejected,
        "document_count": len(extractions),
        "model_tags": model_tags,
        "data_as_of": latest_fetch[:10],
    }
    (out_dir / "site.json").write_text(json.dumps(site, indent=2, sort_keys=True) + "\n")
    return out_dir


def _rejected_detail(source_text: str, quote: str) -> _RejectedDetail:
    """Compare one rejected claim quote with its closest normalized source passage.

    Inputs:
        source_text: Original document text used by the provenance gate.
        quote: Rejected model quote to compare with that source.

    Returns:
        A similarity-only result below the cutoff, or mapped offsets and a word diff.

    Failure mode:
        Normalization and ``difflib`` errors propagate; the exporter never guesses a result.
    """
    ns, index_map = normalize_with_map(source_text)
    nq = normalize(quote)
    if not nq:
        return {"similarity": 0.0, "closest": None}

    match = difflib.SequenceMatcher(None, ns, nq, autojunk=False).find_longest_match(
        0, len(ns), 0, len(nq)
    )
    if match.size == 0:
        return {"similarity": 0.0, "closest": None}

    window_start = max(0, match.a - match.b)
    window_end = min(len(ns), window_start + len(nq))
    window_start = max(0, window_end - len(nq))
    while window_start > 0 and ns[window_start - 1] != " ":
        window_start -= 1
    while window_end < len(ns) and ns[window_end] != " ":
        window_end += 1

    closest_norm = ns[window_start:window_end]
    similarity = round(
        difflib.SequenceMatcher(None, closest_norm, nq, autojunk=False).ratio(),
        4,
    )
    if similarity < 0.35:
        return {"similarity": similarity, "closest": None}

    a_words = closest_norm.split(" ")
    b_words = nq.split(" ")
    ops: list[list[str]] = []
    for kind, a1, a2, b1, b2 in difflib.SequenceMatcher(
        None, a_words, b_words, autojunk=False
    ).get_opcodes():
        if kind == "equal":
            ops.append(["equal", " ".join(a_words[a1:a2])])
        elif kind == "insert":
            ops.append(["model", " ".join(b_words[b1:b2])])
        elif kind == "delete":
            ops.append(["source", " ".join(a_words[a1:a2])])
        elif kind == "replace":
            ops.append(["model", " ".join(b_words[b1:b2])])
            ops.append(["source", " ".join(a_words[a1:a2])])

    return {
        "similarity": similarity,
        "closest_start": index_map[window_start],
        "closest_end": index_map[window_end - 1] + 1,
        "closest_quote": closest_norm,
        "diff": ops,
    }


def export_rejected_details(out_dir: Path) -> None:
    """Export closest-passage comparisons for every rejected claim.

    Inputs:
        out_dir: Static-data directory containing validated claims and document texts.

    Outputs:
        ``rejected-details.json`` beneath ``out_dir``.

    Failure mode:
        Missing/malformed claims or source texts and comparison failures propagate; no
        partial fallback data is published.
    """
    details: dict[str, _RejectedDetail] = {}
    for extraction in load_extractions(out_dir / "claims.json"):
        source_text = (out_dir / "documents" / f"{extraction.document_number}.txt").read_text(
            encoding="utf-8"
        )
        for claim in extraction.claims:
            if not claim.accepted:
                details[claim.claim_id] = _rejected_detail(source_text, claim.quote)

    payload: _RejectedDetailsPayload = {
        "schema_version": 1,
        "method": (
            "A deterministic longest-common-substring anchor (difflib) selects the closest "
            "same-length word-aligned source passage; similarity is the difflib ratio between "
            "the normalized passage and the claim's normalized quote. Entries with similarity "
            "below 0.35 report closest: null instead of a passage."
        ),
        "details": details,
    }
    (out_dir / "rejected-details.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def export_example(out_dir: Path) -> None:
    """Export pinned accepted/rejected examples explaining the provenance gate.

    Inputs:
        out_dir: Static-data directory containing validated claims and document texts.

    Outputs:
        ``example.json`` beneath ``out_dir``.

    Failure mode:
        Missing pins, verdict drift, invalid accepted offsets, missing source text, or
        comparison failures raise before the example is written (fail-closed).
    """
    accepted_claim: ClaimRecord | None = None
    rejected_claim: ClaimRecord | None = None
    for extraction in load_extractions(out_dir / "claims.json"):
        for claim in extraction.claims:
            if claim.claim_id == EXAMPLE_ACCEPTED_CLAIM_ID:
                accepted_claim = claim
            elif claim.claim_id == EXAMPLE_REJECTED_CLAIM_ID:
                rejected_claim = claim

    if accepted_claim is None:
        raise ValueError(f"Example accepted claim {EXAMPLE_ACCEPTED_CLAIM_ID!r} is missing")
    if rejected_claim is None:
        raise ValueError(f"Example rejected claim {EXAMPLE_REJECTED_CLAIM_ID!r} is missing")
    if not accepted_claim.accepted:
        raise ValueError(f"Example accepted claim {EXAMPLE_ACCEPTED_CLAIM_ID!r} is not accepted")
    if rejected_claim.accepted:
        raise ValueError(f"Example rejected claim {EXAMPLE_REJECTED_CLAIM_ID!r} is not rejected")
    if accepted_claim.start is None or accepted_claim.end is None:
        raise ValueError(f"Example accepted claim {EXAMPLE_ACCEPTED_CLAIM_ID!r} has no span")

    accepted_text = (out_dir / "documents" / f"{accepted_claim.document_number}.txt").read_text(
        encoding="utf-8"
    )
    if not 0 <= accepted_claim.start < accepted_claim.end <= len(accepted_text):
        raise ValueError(
            f"Example accepted claim {EXAMPLE_ACCEPTED_CLAIM_ID!r} has invalid offsets"
        )
    excerpt_lo = max(0, accepted_claim.start - 300)
    excerpt_hi = min(len(accepted_text), accepted_claim.end + 300)
    while excerpt_lo > 0 and not accepted_text[excerpt_lo - 1].isspace():
        excerpt_lo -= 1
    while excerpt_hi < len(accepted_text) and not accepted_text[excerpt_hi].isspace():
        excerpt_hi += 1
    accepted: _AcceptedExamplePayload = {
        "claim_id": accepted_claim.claim_id,
        "document_number": accepted_claim.document_number,
        "document_title": accepted_claim.document_title,
        "summary": accepted_claim.summary,
        "quote": accepted_claim.quote,
        "excerpt": accepted_text[excerpt_lo:excerpt_hi],
        "span_start": accepted_claim.start - excerpt_lo,
        "span_end": accepted_claim.end - excerpt_lo,
    }

    rejected_text = (out_dir / "documents" / f"{rejected_claim.document_number}.txt").read_text(
        encoding="utf-8"
    )
    rejected_detail = _rejected_detail(rejected_text, rejected_claim.quote)
    rejected: dict[str, object] = {
        "claim_id": rejected_claim.claim_id,
        "document_number": rejected_claim.document_number,
        "document_title": rejected_claim.document_title,
        "summary": rejected_claim.summary,
        "quote": rejected_claim.quote,
    }
    for key, value in rejected_detail.items():
        rejected[key] = value

    payload: _ExamplePayload = {"accepted": accepted, "rejected": rejected}
    (out_dir / "example.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def export_ogc01_data(settings: Settings, web_dir: Path) -> None:
    """Export EXTEND-OGC01 artifacts (authority, grounding, drafts, texts).

    The U.S.C. section texts and derived part texts are written byte-identical
    to what the provenance gate verified, so UI highlight offsets never drift.
    Failure mode: missing pipeline outputs raise ``FileNotFoundError`` — a
    partial export is never produced silently.
    """
    import shutil

    from reglens.authority.run import AUTHORITY_JSON
    from reglens.draft.run import CONFORMANCE_JSON, DRAFTS_DIR
    from reglens.grounding.run import GROUNDING_JSON
    from reglens.ingest.ecfr import xml_to_text

    out_dir = web_dir / "public" / "data"
    usc_dir = out_dir / "usc"
    parts_dir = out_dir / "authority-parts"
    drafts_out = out_dir / "drafts"
    # A failed rebuild must not leave a derived index describing newer source
    # files alongside an older index.
    for artifact_name in ("sections.json", "search-index.json"):
        (out_dir / artifact_name).unlink(missing_ok=True)
    # Fail-closed publication: every generated text directory mirrors the
    # current accepted/pinned set exactly, so removed inputs cannot remain
    # published or leak into a later search index.
    for directory in (usc_dir, parts_dir, drafts_out):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True, exist_ok=True)

    export = AuthorityExport.model_validate_json(AUTHORITY_JSON.read_text())
    expected_usc_hashes: dict[str, str] = {}
    for part in export.parts:
        for resolved in part.resolved:
            filename = f"usc-{resolved.usc_title}-s{resolved.usc_section}.txt"
            previous_hash = expected_usc_hashes.setdefault(filename, resolved.text_sha256)
            if previous_hash != resolved.text_sha256:
                raise ValueError(f"Conflicting pinned text hashes for {filename}")
    expected_part_hashes = {
        f"{part.cfr_title}-CFR-{part.part}.txt": part.part_text_sha256 for part in export.parts
    }
    (out_dir / "authority.json").write_text(export.model_dump_json(indent=2) + "\n")
    (out_dir / "grounding.json").write_text(GROUNDING_JSON.read_text())
    (out_dir / "conformance.json").write_text(CONFORMANCE_JSON.read_text())
    for draft_path in sorted(DRAFTS_DIR.glob("*.txt")):
        (drafts_out / draft_path.name).write_bytes(draft_path.read_bytes())

    # Grounding scans every FR document, including the four source preambles
    # that carry no extracted claims — export their texts too so marker spans
    # can highlight (claims-corpus texts are exported by export_web_data).
    from reglens.extract.run import discover_documents

    documents_dir = out_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    for pair in discover_documents(settings.data_dir):
        # Always (re)written: a stale copy must never outlive its snapshot.
        (documents_dir / f"{pair.document_number}.txt").write_text(
            pair.text, encoding="utf-8", newline="\n"
        )

    for snapshot_dir, manifest in iter_snapshots(settings.data_dir / "raw"):
        payload_path = _snapshot_payload_path(snapshot_dir, manifest.filename)
        if manifest.content_type == "text/x-usc-section" and manifest.filename.endswith(".txt"):
            expected_hash = expected_usc_hashes.get(manifest.filename)
            if expected_hash is None:
                continue
            payload = payload_path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != expected_hash:
                continue
            (usc_dir / manifest.filename).write_bytes(payload)
        elif manifest.content_type == "application/xml" and "-authority-" in manifest.filename:
            # Same deterministic derivation as reglens.authority.run — byte-identical.
            part_stem = manifest.filename.rsplit("-authority-", 1)[0]
            output_filename = f"{part_stem}.txt"
            expected_hash = expected_part_hashes.get(output_filename)
            if expected_hash is None:
                continue
            text = xml_to_text(payload_path.read_bytes())
            if hashlib.sha256(text.encode()).hexdigest() != expected_hash:
                continue
            (parts_dir / output_filename).write_text(text, encoding="utf-8", newline="\n")

    actual_usc_files = {path.name for path in usc_dir.glob("*.txt")}
    missing_usc_files = sorted(expected_usc_hashes.keys() - actual_usc_files)
    if missing_usc_files:
        raise FileNotFoundError(f"Missing pinned U.S.C. texts: {missing_usc_files}")
    actual_part_files = {path.name for path in parts_dir.glob("*.txt")}
    missing_part_files = sorted(expected_part_hashes.keys() - actual_part_files)
    if missing_part_files:
        raise FileNotFoundError(f"Missing pinned CFR part texts: {missing_part_files}")

    _export_structure_and_search(export, out_dir)


def export_use_case_inventory(settings: Settings, web_dir: Path) -> None:
    """Export the OGC-01 inventory reference JSON from the pinned snapshot.

    Reads only the committed content-addressed snapshot (never the network),
    re-verifies its digest, and writes ``use-case-inventory.json``. Failure
    mode: a missing snapshot, a digest mismatch, or a manifest whose URL or
    digest disagrees with the module pins raises — the About section's
    provenance claims are never published unverified (fail-closed).
    """
    from reglens.ingest.inventory import INVENTORY_URL

    snapshot_dir = settings.data_dir / "raw" / INVENTORY_SNAPSHOT_SHA256
    manifest = read_manifest(snapshot_dir)
    payload = _snapshot_payload_path(snapshot_dir, manifest.filename).read_bytes()
    if hashlib.sha256(payload).hexdigest() != INVENTORY_SNAPSHOT_SHA256:
        # Fail-closed: published provenance must match the committed bytes.
        raise ValueError("use-case inventory snapshot bytes do not match the pinned digest")
    if manifest.sha256 != INVENTORY_SNAPSHOT_SHA256 or manifest.url != INVENTORY_URL:
        # Fail-closed: a stale or edited manifest must never supply the
        # provenance the site displays as the snapshot's identity.
        raise ValueError("use-case inventory manifest does not match the pinned URL/digest")
    data = parse_inventory_csv(payload)
    export = UseCaseInventoryExport(
        source_url=INVENTORY_URL,
        fetched_at=manifest.fetched_at,
        sha256=INVENTORY_SNAPSHOT_SHA256,
        row=data.row,
        context=data.context,
    )
    (web_dir / "public" / "data" / "use-case-inventory.json").write_text(
        export.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> int:
    settings = Settings()
    out_dir = export_web_data(settings, Path("web"))
    export_ogc01_data(settings, Path("web"))
    export_use_case_inventory(settings, Path("web"))
    export_rejected_details(out_dir)
    export_example(out_dir)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
