"""Federal Register API v1 client.

Inputs: a document number (or a search for recent Treasury rules). Outputs:
content-addressed snapshots of the document metadata JSON and its raw full
text. Failure mode: HTTP errors propagate from httpx; URLs outside the
allow-list raise ``DisallowedSourceError`` before any request is made.
"""

import json
import re
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict

from reglens.config import Settings
from reglens.ingest.allowlist import require_allowed
from reglens.ingest.snapshot import write_snapshot

API_BASE = "https://www.federalregister.gov/api/v1"

FR_SCHEMA_VERSION = 1

_DOCUMENT_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def require_safe_document_number(document_number: str) -> str:
    """Reject document numbers that could escape a path or URL segment.

    Fail-closed: values arrive from the CLI and from the remote search API;
    anything outside ``[A-Za-z0-9._-]`` raises rather than becoming a filename.
    """
    if not _DOCUMENT_NUMBER_PATTERN.fullmatch(document_number):
        raise ValueError(f"unsafe document number: {document_number!r}")
    return document_number


class FRDocument(BaseModel):
    """Subset of the Federal Register document payload RegLens relies on.

    Unknown upstream fields are tolerated (``extra="allow"``) so schema drift
    logs rather than breaks; the fields below are the contract.
    """

    model_config = ConfigDict(extra="allow")

    schema_version: int = FR_SCHEMA_VERSION
    document_number: str
    title: str
    publication_date: str
    html_url: str
    raw_text_url: str | None = None


def make_client(settings: Settings) -> httpx.Client:
    """HTTP client with the project User-Agent; the only place headers are set."""
    return httpx.Client(headers={"User-Agent": settings.user_agent}, timeout=30.0)


def fetch_document(client: httpx.Client, document_number: str) -> FRDocument:
    """Fetch one document's metadata by its FR document number."""
    url = f"{API_BASE}/documents/{document_number}.json"
    response = client.get(require_allowed(url))
    response.raise_for_status()
    return FRDocument.model_validate(response.json())


def recent_treasury_rules(client: httpx.Client, count: int = 1) -> list[str]:
    """Document numbers of the ``count`` most recent Treasury final rules.

    Failure mode: raises ``LookupError`` if the search returns no results —
    the caller must pick documents explicitly rather than ingest nothing.
    """
    url = (
        f"{API_BASE}/documents.json"
        "?conditions[agencies][]=treasury-department"
        "&conditions[type][]=RULE"
        f"&order=newest&per_page={count}&fields[]=document_number"
    )
    response = client.get(require_allowed(url))
    response.raise_for_status()
    results: list[dict[str, str]] = response.json().get("results", [])
    if not results:
        raise LookupError("Federal Register search returned no Treasury rules")
    return [require_safe_document_number(result["document_number"]) for result in results]


def find_rule_by_citation(
    client: httpx.Client, volume: int, page: int, publication_date: str
) -> str | None:
    """Resolve an FR citation (e.g. ``62 FR 45101``) to a document number.

    The FR API has no citation-lookup endpoint, so this filters documents
    published on ``publication_date`` and matches ``page`` against each
    result's ``start_page``..``end_page`` range. Failure mode: returns None
    when no published document covers the page (a coverage fact, never a
    guess); HTTP errors propagate.
    """
    url = (
        f"{API_BASE}/documents.json"
        f"?conditions[publication_date][is]={publication_date}"
        "&per_page=300&fields[]=document_number&fields[]=citation"
        "&fields[]=start_page&fields[]=end_page"
    )
    response = client.get(require_allowed(url))
    response.raise_for_status()
    del volume  # citation volume is implied by publication_date; kept for call-site clarity
    for result in response.json().get("results", []):
        start = result.get("start_page")
        end = result.get("end_page") or start
        if isinstance(start, int) and isinstance(end, int) and start <= page <= end:
            return require_safe_document_number(result["document_number"])
    return None


def latest_treasury_rule(client: httpx.Client) -> str:
    """Document number of the most recent Treasury final rule."""
    return recent_treasury_rules(client, count=1)[0]


def rules_amending_part(client: httpx.Client, *, title: int, part: int) -> list[str]:
    """Every Federal Register final rule the FR CFR index attributes to one CFR part.

    This is the corpus inclusion rule expressed as code: re-running it
    reproduces the document set, rather than depending on whichever documents an
    earlier citation-following pass happened to reach. Results are returned in
    the API's newest-first order and de-duplicated by the caller.

    Failure mode: HTTP errors propagate; an unsafe document number raises before
    it can become a filename. Coverage caveat: the index only tags documents
    whose FR metadata carries a CFR reference, so some pre-1994 rules are not
    reachable by this criterion (recorded in docs/DATA_SOURCES.md).
    """
    document_numbers: list[str] = []
    page = 1
    while True:
        query = urlencode(
            {
                "conditions[cfr][title]": title,
                "conditions[cfr][part]": part,
                "conditions[type][]": "RULE",
                "fields[]": "document_number",
                "per_page": 100,
                "page": page,
            }
        )
        response = client.get(require_allowed(f"{API_BASE}/documents.json?{query}"))
        response.raise_for_status()
        payload = response.json()
        results: list[dict[str, str]] = payload.get("results") or []
        for result in results:
            document_numbers.append(require_safe_document_number(result["document_number"]))
        total_pages: int = payload.get("total_pages") or 1
        if page >= total_pages:
            return document_numbers
        page += 1


def corpus_document_numbers(client: httpx.Client, *, title: int, parts: Sequence[int]) -> list[str]:
    """The de-duplicated corpus: every final rule amending any of ``parts``.

    Sorted for determinism so two runs over an unchanged Federal Register
    produce the same ingest order.
    """
    found: set[str] = set()
    for part in parts:
        found.update(rules_amending_part(client, title=title, part=part))
    return sorted(found)


def ingest_document(settings: Settings, document_number: str) -> tuple[Path, Path]:
    """Snapshot one FR document's metadata JSON and raw text; return both snapshot dirs."""
    require_safe_document_number(document_number)
    with make_client(settings) as client:
        document = fetch_document(client, document_number)
        metadata_bytes = json.dumps(document.model_dump(), indent=2, sort_keys=True).encode()
        metadata_dir = write_snapshot(
            settings.data_dir,
            source_id="federal_register",
            url=f"{API_BASE}/documents/{document_number}.json",
            content=metadata_bytes,
            content_type="application/json",
            filename=f"{document_number}.json",
        )
        if document.raw_text_url is None:
            raise LookupError(f"FR document {document_number} has no raw_text_url")
        text_response = client.get(require_allowed(document.raw_text_url))
        text_response.raise_for_status()
        text_dir = write_snapshot(
            settings.data_dir,
            source_id="federal_register",
            url=document.raw_text_url,
            content=text_response.content,
            content_type="text/plain",
            filename=f"{document_number}.txt",
        )
    return metadata_dir, text_dir
