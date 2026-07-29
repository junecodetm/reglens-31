"""Pinned OLRC U.S. Code title and section ingest.

Inputs: an OLRC release point, a title number, and exact U.S. Code section
identifiers. Outputs: a locally cached USLM title archive plus
content-addressed text and JSON snapshots for every found section. Failure
mode: malformed release points, HTTP/ZIP/XML errors, archives without USLM
XML, and non-ZIP responses raise; excluded or missing sections are never
guessed or synthesized.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

import httpx
from pydantic import BaseModel

from reglens.config import Settings
from reglens.ingest.allowlist import require_allowed
from reglens.ingest.snapshot import write_snapshot

USLM_NAMESPACE = "http://xml.house.gov/schemas/uslm/1.0"
_SECTION_TAG = f"{{{USLM_NAMESPACE}}}section"
_HEADING_TAG = f"{{{USLM_NAMESPACE}}}heading"
_SUBSECTION_TAG = f"{{{USLM_NAMESPACE}}}subsection"
_EXCLUDED_TAGS = {
    f"{{{USLM_NAMESPACE}}}notes",
    f"{{{USLM_NAMESPACE}}}sourceCredit",
}
_RELEASE_POINT = re.compile(r"\d+-\d+")
_ROOT_CLEAR_INTERVAL = 256


class UscSection(BaseModel):
    """One exact U.S. Code section extracted from a pinned USLM title archive."""

    title: int
    section: str
    identifier: str
    heading: str | None
    status: str | None
    text: str


def _title_number(title: int) -> str:
    return f"{title:02d}"


def title_zip_url(release_point: str, title: int) -> str:
    """Return the pinned OLRC USLM XML archive URL for one U.S. Code title."""
    if _RELEASE_POINT.fullmatch(release_point) is None:
        # Fail-closed: an invalid release point must never select an implicit
        # or moving U.S. Code archive.
        raise ValueError(f"invalid U.S. Code release point: {release_point}")
    congress, law = release_point.split("-", maxsplit=1)
    title_number = _title_number(title)
    return (
        "https://uscode.house.gov/download/releasepoints/us/pl/"
        f"{congress}/{law}/xml_usc{title_number}@{release_point}.zip"
    )


# Ceilings: a single title archive (largest real zips ~100 MB compressed)
# and its uncompressed XML member (largest real titles ~700 MB). Past these,
# a compromised origin is feeding a decompression/disk bomb.
_MAX_ZIP_BYTES = 400 * 1024 * 1024
_MAX_XML_MEMBER_BYTES = 1600 * 1024 * 1024


def recheck_redirects(response: httpx.Response) -> None:
    """httpx response hook: every redirect hop must stay on the allow-list.

    Fail-closed: ``require_allowed`` raises on the first off-list hop, so a
    redirect can never smuggle a fetch to an unapproved host.
    """
    if response.is_redirect and response.next_request is not None:
        require_allowed(str(response.next_request.url))


def fetch_title_zip(settings: Settings, title: int) -> Path:
    """Download and cache one pinned USLM title ZIP, or replay the cached file."""
    title_number = _title_number(title)
    release_point = settings.usc_release_point
    if _RELEASE_POINT.fullmatch(release_point) is None:
        # Fail-closed BEFORE any path construction: a hostile release-point
        # value must never shape the cache path.
        raise ValueError(f"invalid U.S. Code release point: {release_point}")
    cache_path = settings.data_dir / "cache" / f"xml_usc{title_number}@{release_point}.zip"
    digest_path = cache_path.with_suffix(".zip.sha256")
    if cache_path.is_file():
        # Fail-closed replay: the cached archive must match the digest
        # recorded at first fetch — a tampered cache is refused, not parsed.
        if not digest_path.is_file():
            raise ValueError(f"cached archive has no recorded digest: {cache_path}")
        actual = hashlib.sha256(cache_path.read_bytes()).hexdigest()
        recorded = digest_path.read_text().strip()
        if actual != recorded:
            raise ValueError(f"cached archive digest mismatch: {cache_path}")
        return cache_path

    url = title_zip_url(release_point, title)
    allowed_url = require_allowed(url)
    with (
        httpx.Client(
            headers={"User-Agent": settings.user_agent},
            timeout=300,
            follow_redirects=True,
            event_hooks={"response": [recheck_redirects]},
        ) as client,
        client.stream("GET", allowed_url) as response,
    ):
        response.raise_for_status()
        chunks = response.iter_bytes(chunk_size=64 * 1024)
        first_chunk = next(chunks, b"")
        if not first_chunk.startswith(b"PK"):
            # Fail-closed: an HTML error or interstitial page must never be
            # cached on disk as if it were a valid ZIP archive.
            raise ValueError(f"U.S. Code title {title} fetch did not return a ZIP: {url}")

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path = cache_path.with_name(f".{cache_path.name}.part")
        try:
            # Fail-closed: only a completely streamed archive is promoted
            # to the replay cache; an interrupted download remains unusable.
            digest = hashlib.sha256()
            total = len(first_chunk)
            with partial_path.open("wb") as archive_file:
                archive_file.write(first_chunk)
                digest.update(first_chunk)
                for chunk in chunks:
                    total += len(chunk)
                    if total > _MAX_ZIP_BYTES:
                        # Fail-closed: an implausibly large stream is refused.
                        raise ValueError(f"title {title} archive exceeds size ceiling")
                    archive_file.write(chunk)
                    digest.update(chunk)
            partial_path.replace(cache_path)
            digest_path.write_text(digest.hexdigest() + "\n")
        finally:
            partial_path.unlink(missing_ok=True)
    return cache_path


def _stripped_text(element: ElementTree.Element[str]) -> str | None:
    text = " ".join(fragment.strip() for fragment in element.itertext() if fragment.strip())
    return text or None


def _remove_nonstatutory_subtrees(element: ElementTree.Element[str]) -> None:
    for child in list(element):
        if child.tag in _EXCLUDED_TAGS:
            # Fail-closed/correctness: editorial notes and source credits must
            # never be quotable as statutory text; the provenance gate treats
            # verbatim quotability as meaningful.
            element.remove(child)
        else:
            _remove_nonstatutory_subtrees(child)


def _flatten_section(element: ElementTree.Element[str]) -> str:
    fragments: list[str] = []

    def visit(node: ElementTree.Element[str], *, root: bool = False) -> None:
        if not root and node.tag == _SUBSECTION_TAG:
            fragments.append("\n\n")
        if node.text is not None and (text := node.text.strip()):
            fragments.append(text)
        for child in node:
            visit(child)
            if child.tail is not None and (tail := child.tail.strip()):
                fragments.append(tail)

    visit(element, root=True)
    return re.sub(r" *\n\n *", "\n\n", " ".join(fragments))


def _clear_finished_root_children(
    root: ElementTree.Element[str],
    finished_children: list[ElementTree.Element[str]],
) -> None:
    for child in finished_children:
        child.clear()
        root.remove(child)
    finished_children.clear()


def extract_sections(zip_path: Path, title: int, sections: set[str]) -> dict[str, UscSection]:
    """Extract exactly requested sections; requested sections not present stay absent."""
    identifiers = {f"/us/usc/t{title}/s{section}": section for section in sections}
    found: dict[str, UscSection] = {}

    with zipfile.ZipFile(zip_path) as archive:
        xml_members = [
            member
            for member in archive.infolist()
            if not member.is_dir() and member.filename.casefold().endswith(".xml")
        ]
        if not xml_members:
            # Fail-closed: an archive without USLM XML must never be treated as
            # a valid title containing no requested sections.
            raise ValueError(f"U.S. Code archive contains no XML member: {zip_path}")
        xml_member = max(xml_members, key=lambda member: (member.file_size, member.filename))
        if xml_member.file_size > _MAX_XML_MEMBER_BYTES:
            # Fail-closed: a member claiming an implausible uncompressed size
            # is a decompression bomb, not a U.S. Code title.
            raise ValueError(f"U.S. Code XML member exceeds size ceiling: {xml_member.filename}")

        with archive.open(xml_member) as xml_file:
            root: ElementTree.Element[str] | None = None
            stack: list[ElementTree.Element[str]] = []
            finished_root_children: list[ElementTree.Element[str]] = []
            finished_elements = 0
            parser = ElementTree.iterparse(xml_file, events=("start", "end"))
            for event, element in parser:
                if event == "start":
                    if root is None:
                        root = element
                    stack.append(element)
                    continue

                parent = stack[-2] if len(stack) > 1 else None
                if element.tag == _SECTION_TAG:
                    identifier = cast(str | None, element.get("identifier"))
                    # Match only the canonical identifier: heading text can be
                    # missing or duplicated, so it is not a reliable section key.
                    section = identifiers.get(identifier) if identifier is not None else None
                    if identifier is not None and section is not None:
                        heading_element = element.find(_HEADING_TAG)
                        heading = (
                            _stripped_text(heading_element) if heading_element is not None else None
                        )
                        _remove_nonstatutory_subtrees(element)
                        found[section] = UscSection(
                            title=title,
                            section=section,
                            identifier=identifier,
                            heading=heading,
                            status=element.get("status"),
                            text=_flatten_section(element),
                        )
                    element.clear()
                    if parent is not None:
                        parent.remove(element)
                elif root is not None and parent is root:
                    finished_root_children.append(element)

                stack.pop()
                finished_elements += 1
                if root is not None and finished_elements % _ROOT_CLEAR_INTERVAL == 0:
                    # Clear only children whose end events were consumed; the
                    # parser may already have attached future buffered siblings.
                    _clear_finished_root_children(root, finished_root_children)
            if root is not None:
                _clear_finished_root_children(root, finished_root_children)

    return found


def snapshot_sections(settings: Settings, title: int, sections: set[str]) -> dict[str, Path]:
    """Cache a title and snapshot text plus JSON for every requested section found."""
    zip_path = fetch_title_zip(settings, title)
    extracted = extract_sections(zip_path, title, sections)
    archive_url = title_zip_url(settings.usc_release_point, title)
    text_dirs: dict[str, Path] = {}
    for section in sorted(extracted):
        usc_section = extracted[section]
        section_url = f"{archive_url}#{usc_section.identifier}"
        # Fail-closed: the custom type prevents discover_documents from
        # pairing this authority text as a regular claims-corpus document.
        text_dirs[section] = write_snapshot(
            settings.data_dir,
            source_id="uscode",
            url=section_url,
            content=usc_section.text.encode(),
            content_type="text/x-usc-section",
            filename=f"usc-{title}-s{section}.txt",
        )
        # Fail-closed: the custom JSON type likewise prevents accidental
        # claims-corpus metadata pairing by discover_documents.
        write_snapshot(
            settings.data_dir,
            source_id="uscode",
            url=section_url,
            content=usc_section.model_dump_json(indent=2).encode(),
            content_type="application/x-usc-section+json",
            filename=f"usc-{title}-s{section}.json",
        )
    return text_dirs
