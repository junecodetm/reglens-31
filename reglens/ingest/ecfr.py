"""eCFR Title 31 ingest via the eCFR versioner API.

Inputs: a part number within Title 31 and a pinned point-in-time date.
Outputs: content-addressed snapshots of a small metadata record and the
part's plain text. Failure mode: HTTP errors propagate; URLs are checked
against the allow-list before any request; XML that cannot be parsed raises
(nothing is snapshotted from unparseable input).

Note: the eCFR is an unofficial editorial compilation (docs/DATA_SOURCES.md);
the UI links to the eCFR page for human verification.
"""

import json
import re
from pathlib import Path
from xml.etree import ElementTree

import httpx

from reglens.config import Settings
from reglens.ingest.allowlist import require_allowed
from reglens.ingest.snapshot import write_snapshot

API_BASE = "https://www.ecfr.gov/api/versioner/v1"


def part_url(date: str, part: int) -> str:
    """Point-in-time full XML URL for one part of Title 31."""
    return f"{API_BASE}/full/{date}/title-31.xml?part={part}"


def xml_to_text(xml_bytes: bytes) -> str:
    """Flatten eCFR XML to plain text, preserving paragraph breaks.

    Failure mode: ``ElementTree.ParseError`` propagates — malformed XML is
    never silently coerced into text. Python's parser does not resolve external
    entities (no XXE); internal entity expansion is bounded only by parser
    defaults, acceptable for this fixed, allow-listed https government source.
    """
    root = ElementTree.fromstring(xml_bytes)
    text = " ".join(fragment.strip() for fragment in root.itertext() if fragment.strip())
    return re.sub(r" (?=(Sec\.|§))", "\n\n", text)


def ingest_part(settings: Settings, part: int, date: str | None = None) -> tuple[Path, Path]:
    """Snapshot one Title 31 part's metadata and plain text; return both snapshot dirs."""
    pinned_date = date or settings.ecfr_date
    url = part_url(pinned_date, part)
    document_number = f"31-CFR-{part}"
    with httpx.Client(headers={"User-Agent": settings.user_agent}, timeout=120.0) as client:
        response = client.get(require_allowed(url))
        response.raise_for_status()
        text = xml_to_text(response.content)
    metadata = {
        "document_number": document_number,
        "title": f"31 CFR Part {part} (point-in-time {pinned_date})",
        "html_url": f"https://www.ecfr.gov/current/title-31/part-{part}",
    }
    metadata_dir = write_snapshot(
        settings.data_dir,
        source_id="ecfr",
        url=url,
        content=json.dumps(metadata, indent=2, sort_keys=True).encode(),
        content_type="application/json",
        filename=f"{document_number}.json",
    )
    text_dir = write_snapshot(
        settings.data_dir,
        source_id="ecfr",
        url=url,
        content=text.encode(),
        content_type="text/plain",
        filename=f"{document_number}.txt",
    )
    return metadata_dir, text_dir
