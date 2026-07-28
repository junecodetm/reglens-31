"""Federal Register API v1 client.

Inputs: a document number (or a search for recent Treasury rules). Outputs:
content-addressed snapshots of the document metadata JSON and its raw full
text. Failure mode: HTTP errors propagate from httpx; URLs outside the
allow-list raise ``DisallowedSourceError`` before any request is made.
"""

import json
import re
from pathlib import Path

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


def latest_treasury_rule(client: httpx.Client) -> str:
    """Document number of the most recent Treasury final rule."""
    return recent_treasury_rules(client, count=1)[0]


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
