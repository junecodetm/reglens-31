"""Export processed records and source texts as static assets for the web UI.

Inputs: ``data/processed/claims.json`` and the raw snapshots it references.
Outputs: ``web/public/data/claims.json``, ``web/public/data/documents/<n>.txt``
and ``web/public/data/site.json`` plus the OGC01 authority assets, CFR section
structure, and lexical search index. Counts, model tags, and "as of" dates come
from persisted inputs, never wall-clock time. Failure mode: missing inputs raise
``FileNotFoundError``; malformed records raise ``ValidationError``; parts with
no sections and search indexes larger than 4 MiB raise ``ValueError``.
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from reglens.authority.records import AuthorityExport
from reglens.config import Settings
from reglens.extract.records import DocumentExtraction, load_extractions
from reglens.ingest.federal_register import require_safe_document_number
from reglens.ingest.snapshot import read_manifest
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
    """Copy claims, per-document text, and site metadata into ``web/public/data``."""
    claims_path = settings.data_dir / "processed" / "claims.json"
    extractions = [_sanitized(extraction) for extraction in load_extractions(claims_path)]

    out_dir = web_dir / "public" / "data"
    documents_dir = out_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    by_sha = {extraction.document_sha256: extraction for extraction in extractions}
    latest_fetch = ""
    for snapshot_dir in sorted((settings.data_dir / "raw").iterdir()):
        if (snapshot_dir / "manifest.json").is_file():
            manifest = read_manifest(snapshot_dir)
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

    raw_root = settings.data_dir / "raw"
    for snapshot_dir in sorted(raw_root.iterdir()):
        if not (snapshot_dir / "manifest.json").is_file():
            continue
        manifest = read_manifest(snapshot_dir)
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
    mode: a missing or digest-mismatched snapshot raises — the About
    section's provenance claims are never published unverified (fail-closed).
    """
    snapshot_dir = settings.data_dir / "raw" / INVENTORY_SNAPSHOT_SHA256
    manifest = read_manifest(snapshot_dir)
    payload = _snapshot_payload_path(snapshot_dir, manifest.filename).read_bytes()
    if hashlib.sha256(payload).hexdigest() != INVENTORY_SNAPSHOT_SHA256:
        # Fail-closed: published provenance must match the committed bytes.
        raise ValueError("use-case inventory snapshot bytes do not match the pinned digest")
    data = parse_inventory_csv(payload)
    export = UseCaseInventoryExport(
        source_url=manifest.url,
        fetched_at=manifest.fetched_at,
        sha256=manifest.sha256,
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
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
