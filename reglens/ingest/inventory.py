"""Treasury AI Use Case Inventory reference snapshot.

Inputs: none (the source URL is pinned below). Outputs: a content-addressed
snapshot of Treasury's public AI Use Case Inventory CSV — the primary source
for the site's "About this demonstration" framing of use case OGC-01
"Regulatory Reform Tool". Failure mode: HTTP errors propagate; the URL is
allow-list-checked before the request; a payload that does not contain the
OGC-01 inventory row raises rather than snapshotting an error page.

This is a one-time reference snapshot (U.S. Government work), not a pipeline
input: the exporter reads only the committed snapshot, never the network.
"""

from pathlib import Path

import httpx

from reglens.config import Settings
from reglens.ingest.allowlist import require_allowed
from reglens.ingest.snapshot import write_snapshot
from reglens.ingest.uscode import recheck_redirects

INVENTORY_URL = "https://home.treasury.gov/system/files/136/Treasury-AI-Use-Case-Inventory.csv"
INVENTORY_FILENAME = "Treasury-AI-Use-Case-Inventory.csv"


def ingest_use_case_inventory(settings: Settings) -> Path:
    """Snapshot the Treasury AI Use Case Inventory CSV; return the snapshot dir."""
    with httpx.Client(
        headers={"User-Agent": settings.user_agent},
        timeout=120.0,
        # Every redirect hop is re-checked against the allow-list (fail-closed).
        event_hooks={"response": [recheck_redirects]},
    ) as client:
        response = client.get(require_allowed(INVENTORY_URL), follow_redirects=True)
        response.raise_for_status()
        text = response.content.decode("utf-8-sig", errors="replace")
        if text.lstrip().startswith("<") or "OGC-01" not in text:
            # Fail-closed: an HTML error/challenge page or a restructured file
            # without the OGC-01 row must never be snapshotted as the inventory.
            raise ValueError(f"inventory fetch did not return the expected CSV: {INVENTORY_URL}")
        return write_snapshot(
            settings.data_dir,
            source_id="use-case-inventory",
            url=INVENTORY_URL,
            content=response.content,
            content_type="text/csv",
            filename=INVENTORY_FILENAME,
        )
