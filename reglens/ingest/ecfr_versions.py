"""eCFR currency sources: per-section amendment history and the official section census.

Inputs: none (every URL is derived from :data:`reglens.corpus.CFR_PARTS` and
``Settings.ecfr_date``). Outputs: one content-addressed snapshot per API
response plus ``data/reference/ecfr-currency-sources.json``, the committed
index that records each response's URL and SHA-256.

Failure mode: HTTP errors propagate; every URL is allow-list-checked before the
request; a response that is not the expected JSON shape raises rather than
being snapshotted. Nothing is written until every fetch has succeeded, so a
partial refresh cannot leave a half-updated index.

Why both endpoints: ``versions`` supplies each section's amendment date, which
is what makes staleness measurable against the pinned snapshot date;
``structure`` supplies the authoritative section census, which
``reglens.structure``'s parser is checked against (see tests/test_ecfr_census.py).
That check is the point — it turns a self-asserted section count into an
externally sourced one.
"""

import json
from pathlib import Path
from typing import Final

import httpx
from pydantic import BaseModel, ConfigDict

from reglens.config import Settings
from reglens.corpus import CFR_PARTS, CFR_TITLE
from reglens.ingest.allowlist import require_allowed
from reglens.ingest.snapshot import content_sha256, write_snapshot

API_BASE: Final = "https://www.ecfr.gov/api/versioner/v1"
SOURCE_ID: Final = "ecfr-currency"
SOURCE_INDEX_PATH: Final = Path("reference") / "ecfr-currency-sources.json"


class VersionRecord(BaseModel):
    """One row of the versioner's ``content_versions`` list (unknown fields ignored)."""

    model_config = ConfigDict(extra="ignore")

    type: str
    identifier: str
    amendment_date: str
    removed: bool = False


class VersionsResponse(BaseModel):
    """The ``versions`` endpoint payload for one part."""

    model_config = ConfigDict(extra="ignore")

    content_versions: list[VersionRecord]


class StructureNode(BaseModel):
    """One node of the ``structure`` endpoint's tree (unknown fields ignored)."""

    model_config = ConfigDict(extra="ignore")

    type: str
    identifier: str | None = None
    children: list["StructureNode"] | None = None


class CurrencySource(BaseModel):
    """One snapshotted API response: what it is, where it came from, and its digest."""

    kind: str
    part: int
    url: str
    sha256: str


class CurrencySourceIndex(BaseModel):
    """The committed set of snapshots a currency baseline is derived from."""

    schema_version: int = 1
    snapshot_date: str
    sources: list[CurrencySource]


def versions_url(part: int) -> str:
    """Amendment history for every section of one part."""
    return f"{API_BASE}/versions/title-{CFR_TITLE}.json?part={part}"


def structure_url(date: str, part: int) -> str:
    """The authoritative structure tree for one part at a point in time."""
    return f"{API_BASE}/structure/{date}/title-{CFR_TITLE}.json?part={part}"


def parse_versions(content: bytes) -> VersionsResponse:
    """Typed ``versions`` payload. Failure mode: ``ValidationError`` on any other shape."""
    return VersionsResponse.model_validate_json(content)


def parse_structure(content: bytes) -> StructureNode:
    """Typed ``structure`` payload. Failure mode: ``ValidationError`` on any other shape."""
    return StructureNode.model_validate_json(content)


def _validate(kind: str, content: bytes, url: str) -> None:
    """Reject a response that is not the documented shape, before it is snapshotted.

    Fail-closed: an error page or a restructured payload raises rather than
    being recorded as data.
    """
    if kind == "versions":
        if not parse_versions(content).content_versions:
            raise ValueError(f"eCFR versions response has no content_versions: {url}")
    elif not parse_structure(content).type:
        raise ValueError(f"eCFR structure response is not a node tree: {url}")


def ingest_currency_sources(settings: Settings) -> Path:
    """Snapshot every currency source and write the committed source index.

    Returns the path of the written index. Fetches are completed and validated
    before anything is persisted, so a mid-run failure leaves the previous
    index and snapshots untouched.
    """
    requests = [(kind, part) for part in CFR_PARTS for kind in ("versions", "structure")]
    fetched: list[tuple[str, int, str, bytes]] = []
    with httpx.Client(
        headers={"User-Agent": settings.user_agent, "Accept": "application/json"},
        timeout=120.0,
    ) as client:
        for kind, part in requests:
            url = (
                versions_url(part)
                if kind == "versions"
                else structure_url(settings.ecfr_date, part)
            )
            response = client.get(require_allowed(url))
            response.raise_for_status()
            _validate(kind, response.content, url)
            fetched.append((kind, part, url, response.content))

    sources: list[CurrencySource] = []
    for kind, part, url, content in fetched:
        write_snapshot(
            settings.data_dir,
            source_id=SOURCE_ID,
            url=url,
            content=content,
            content_type="application/json",
            filename=f"ecfr-{kind}-{CFR_TITLE}-{part}.json",
        )
        sources.append(
            CurrencySource(kind=kind, part=part, url=url, sha256=content_sha256(content))
        )

    index = CurrencySourceIndex(snapshot_date=settings.ecfr_date, sources=sources)
    index_path = settings.data_dir / SOURCE_INDEX_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index.model_dump(), indent=2, sort_keys=True) + "\n")
    return index_path


def load_source_index(data_dir: Path) -> CurrencySourceIndex:
    """The committed source index. Failure mode: missing or malformed raises."""
    return CurrencySourceIndex.model_validate_json((data_dir / SOURCE_INDEX_PATH).read_text())


def read_source_bytes(data_dir: Path, source: CurrencySource) -> bytes:
    """One snapshotted response, re-verified against the digest the index records.

    Failure mode: a missing snapshot or any digest mismatch raises — a currency
    claim is never published from bytes that are not provably the ones fetched.
    """
    filename = f"ecfr-{source.kind}-{CFR_TITLE}-{source.part}.json"
    content = (data_dir / "raw" / source.sha256 / filename).read_bytes()
    if content_sha256(content) != source.sha256:
        raise ValueError(f"currency snapshot bytes do not match the recorded digest: {source.url}")
    return content


def main() -> int:
    """CLI: refresh every currency snapshot and the committed source index."""
    settings = Settings()
    index_path = ingest_currency_sources(settings)
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
