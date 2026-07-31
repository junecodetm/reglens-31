"""Authority-linking pipeline: citations → USLM resolution → classification.

Inputs: the per-part authority snapshots (``ingest_part_authority``) and the
pinned OLRC USLM release point. Outputs: ``data/processed/authority.json``
(:class:`AuthorityExport`) plus content-addressed snapshots of every cited
U.S.C. section. Failure mode: fail-closed everywhere — an unresolvable
citation is recorded as ``unresolved`` (never guessed), and a verb-phrase
quote that fails the provenance gate is recorded as a gate rejection (never
downgraded to a softer classification).
"""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from reglens.authority.citations import (
    extract_authority_text,
    extract_part_heading,
    locate_authority_span,
    parse_authority,
)
from reglens.authority.classify import classify_section
from reglens.authority.records import (
    AuthorityCitation,
    AuthorityExport,
    CitationKind,
    PartAuthority,
    ResolvedSection,
)
from reglens.config import Settings
from reglens.corpus import CFR_PARTS
from reglens.ingest.ecfr import xml_to_text
from reglens.ingest.snapshot import iter_snapshots, read_manifest
from reglens.ingest.uscode import UscSection, extract_sections, fetch_title_zip, title_zip_url
from reglens.provenance import verify_span

PARTS = CFR_PARTS
AUTHORITY_JSON = Path("data/processed/authority.json")


def _find_snapshot(data_dir: Path, filename: str) -> tuple[Path, str]:
    """Locate a snapshot dir by exact manifest filename; return (dir, sha256).

    Failure mode: raises ``LookupError`` when absent — the pipeline must not
    proceed on a missing snapshot.
    """
    for snapshot_dir, manifest in iter_snapshots(data_dir / "raw"):
        if manifest.filename == filename:
            return snapshot_dir, manifest.sha256
    raise LookupError(f"no snapshot found for {filename}")


def _resolve_and_classify(section: UscSection, section_sha: str) -> ResolvedSection:
    """Classify one resolved section; gate-verify the winning verb phrase."""
    classification, best, spans = classify_section(section.text)
    resolved = ResolvedSection(
        usc_title=section.title,
        usc_section=section.section,
        identifier=section.identifier,
        heading=section.heading,
        status=section.status,
        text_sha256=section_sha,
        classification=classification,
        grant_spans=spans,
    )
    if best is not None:
        gate = verify_span(section.text, best.quote)
        if gate.accepted and gate.start is not None and gate.end is not None:
            resolved.verb_quote = best.quote
            resolved.verb_start = gate.start
            resolved.verb_end = gate.end
        else:
            # Fail-closed: a quote that fails the exact-substring check rejects
            # the classification outright; it is surfaced in the rejection
            # counter and never downgraded.
            resolved.gate_rejected = True
            resolved.rejection_reason = gate.reason
    return resolved


def resolve_part_citations(
    citations: list[AuthorityCitation],
    sections: dict[tuple[int, str], tuple[UscSection, str]],
) -> tuple[list[ResolvedSection], list[AuthorityCitation], dict[str, int]]:
    """Resolve one part's citations against the extracted USLM sections.

    Failure mode (DoD #2): a ``usc_section`` citation with no matching USLM
    section lands in the ``unresolved`` list untouched — it is never guessed
    at, classified, or quoted (fail-closed).
    """
    resolved: list[ResolvedSection] = []
    unresolved: list[AuthorityCitation] = []
    totals = {"sections": 0, "resolved": 0, "unresolved": 0, "other": 0, "gate_rejections": 0}
    seen: set[tuple[int, str]] = set()
    for citation in citations:
        if citation.kind is not CitationKind.usc_section:
            totals["other"] += 1
            continue
        if citation.usc_title is None or citation.usc_section is None:
            # Fail-closed: a section citation without a (title, section) is a
            # parser defect, never silently skipped or guessed at.
            raise ValueError(f"usc_section citation missing title/section: {citation.raw!r}")
        key = (citation.usc_title, citation.usc_section)
        if key in seen:
            continue  # within-part duplicate: counted once
        seen.add(key)
        totals["sections"] += 1
        entry = sections.get(key)
        if entry is None:
            # Fail-closed: absent from the pinned USLM release point —
            # recorded as unresolved coverage, never guessed at.
            unresolved.append(citation)
            totals["unresolved"] += 1
            continue
        record = _resolve_and_classify(entry[0], entry[1])
        if record.gate_rejected:
            totals["gate_rejections"] += 1
        resolved.append(record)
        totals["resolved"] += 1
    return resolved, unresolved, totals


def build_authority(settings: Settings) -> AuthorityExport:
    """Run authority linking end to end over the in-scope parts."""
    from reglens.ingest.snapshot import write_snapshot  # local: the only writer here

    date = settings.ecfr_authority_date
    part_inputs: list[tuple[int, str, str, str, int, int, list[AuthorityCitation]]] = []
    wanted: dict[int, set[str]] = defaultdict(set)
    for part in PARTS:
        stem = f"31-CFR-{part}-authority-{date}"
        xml_dir, _ = _find_snapshot(settings.data_dir, f"{stem}.xml")
        xml_bytes = (xml_dir / f"{stem}.xml").read_bytes()
        # The part text is DERIVED deterministically from the XML snapshot
        # (same flattener as ingest). A separate .txt snapshot may not exist:
        # content-addressed storage dedupes it against the claims corpus when
        # the part is unchanged between the two pinned dates.
        part_text = xml_to_text(xml_bytes)
        text_sha = hashlib.sha256(part_text.encode()).hexdigest()
        authority_text = extract_authority_text(xml_bytes)
        heading = extract_part_heading(xml_bytes)
        start, end = locate_authority_span(part_text, authority_text)
        citations = parse_authority(authority_text)
        part_inputs.append((part, heading, text_sha, authority_text, start, end, citations))
        for citation in citations:
            if citation.kind is CitationKind.usc_section and citation.usc_section:
                if citation.usc_title is None:
                    raise ValueError(f"usc_section citation missing title: {citation.raw!r}")
                wanted[citation.usc_title].add(citation.usc_section)

    # Resolve every cited section against the pinned release point, snapshot
    # the fragment text, and classify. One parse per title.
    sections: dict[tuple[int, str], tuple[UscSection, str]] = {}
    for title in sorted(wanted):
        zip_path = fetch_title_zip(settings, title)
        found = extract_sections(zip_path, title, wanted[title])
        for number, usc_section in found.items():
            text_dir = write_snapshot(
                settings.data_dir,
                source_id="uscode",
                url=f"{title_zip_url(settings.usc_release_point, title)}#{usc_section.identifier}",
                content=usc_section.text.encode(),
                content_type="text/x-usc-section",
                filename=f"usc-{title}-s{number}.txt",
            )
            sections[(title, number)] = (usc_section, read_manifest(text_dir).sha256)

    parts_out: list[PartAuthority] = []
    gate_rejections = 0
    totals = {"sections": 0, "resolved": 0, "unresolved": 0, "other": 0}
    for part, heading, text_sha, authority_text, start, end, citations in part_inputs:
        resolved, unresolved, part_totals = resolve_part_citations(citations, sections)
        gate_rejections += part_totals["gate_rejections"]
        for key in ("sections", "resolved", "unresolved", "other"):
            totals[key] += part_totals[key]
        parts_out.append(
            PartAuthority(
                part=part,
                part_heading=heading,
                ecfr_date=date,
                authority_text=authority_text,
                part_text_sha256=text_sha,
                authority_start=start,
                authority_end=end,
                citations=citations,
                resolved=resolved,
                unresolved=unresolved,
                ecfr_url=f"https://www.ecfr.gov/on/{date}/title-31/part-{part}",
            )
        )

    return AuthorityExport(
        usc_release_point=settings.usc_release_point,
        generated_from=f"eCFR point-in-time {date}; USLM release point "
        f"{settings.usc_release_point}",
        parts=parts_out,
        total_section_citations=totals["sections"],
        total_resolved=totals["resolved"],
        total_unresolved=totals["unresolved"],
        total_non_section_citations=totals["other"],
        gate_rejections=gate_rejections,
    )


def main() -> int:
    settings = Settings()
    export = build_authority(settings)
    AUTHORITY_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUTHORITY_JSON.write_text(export.model_dump_json(indent=2) + "\n")
    counts = json.loads(export.model_dump_json())
    print(
        f"authority: {counts['total_resolved']} resolved / "
        f"{counts['total_unresolved']} unresolved / "
        f"{counts['total_non_section_citations']} non-section / "
        f"{counts['gate_rejections']} gate rejections"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
