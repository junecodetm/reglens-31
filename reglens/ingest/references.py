"""Fixed reference-document snapshots for EXTEND-OGC01.

Inputs: none (the reference set is pinned below). Outputs: content-addressed
snapshots of the Document Drafting Handbook PDF and the two reginfo.gov
E.O. 14192 accounting PDFs. Failure mode: HTTP errors propagate; URLs are
allow-list-checked before any request; a payload that is not ``%PDF`` raises
rather than snapshotting an error page.

These PDFs provenance the draft-skeleton template rules (DDH, Aug 2018 ed.
rev. 2.2) and the offset-accounting stub's field names (E.O. 14192 Table 1).
"""

from pathlib import Path

import httpx

from reglens.config import Settings
from reglens.ingest.allowlist import require_allowed
from reglens.ingest.snapshot import write_snapshot
from reglens.ingest.uscode import recheck_redirects

REFERENCE_PDFS: tuple[tuple[str, str], ...] = (
    (
        "ddh-aug-2018-rev-2.2",
        "https://www.archives.gov/files/federal-register/write/handbook/ddh.pdf",
    ),
    (
        "eo14192-final-accounting-fy2025",
        "https://www.reginfo.gov/public/pdf/eo14192/Final_Accounting_for_Fiscal_Year_2025_under_EO_14192.pdf",
    ),
    (
        "eo14192-accounting-methods",
        "https://www.reginfo.gov/public/pdf/eo14192/Accounting_Methods_under_EO_14192.pdf",
    ),
)


def ingest_references(settings: Settings) -> list[Path]:
    """Snapshot every pinned reference PDF; return the snapshot directories."""
    snapshot_dirs: list[Path] = []
    with httpx.Client(
        headers={"User-Agent": settings.user_agent},
        timeout=120.0,
        # Every redirect hop is re-checked against the allow-list (fail-closed).
        event_hooks={"response": [recheck_redirects]},
    ) as client:
        for stem, url in REFERENCE_PDFS:
            response = client.get(require_allowed(url), follow_redirects=True)
            response.raise_for_status()
            if not response.content.startswith(b"%PDF"):
                # Fail-closed: an HTML error/challenge page must never be
                # snapshotted as if it were the reference document.
                raise ValueError(f"reference fetch for {stem} did not return a PDF: {url}")
            snapshot_dirs.append(
                write_snapshot(
                    settings.data_dir,
                    source_id="references",
                    url=url,
                    content=response.content,
                    content_type="application/pdf",
                    filename=f"{stem}.pdf",
                )
            )
    return snapshot_dirs
