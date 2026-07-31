"""Runtime enforcement of the data-source allow-list.

Inputs: a candidate URL. Outputs: pass/refuse. Failure mode: any URL outside
the docs/DATA_SOURCES.md table raises :class:`DisallowedSourceError`.

This enforces the NO-RESTRICTED-DATA invariant (CLAUDE.md §2, invariant 3):
only the documented public sources are fetchable. Fail-closed: malformed
URLs, non-https schemes, and unknown hosts are all refused, never passed.
"""

from urllib.parse import urlsplit


class DisallowedSourceError(RuntimeError):
    """Raised when a URL is outside the docs/DATA_SOURCES.md allow-list."""


# (exact host, required path prefix) pairs — one or more per allowed source.
_ALLOWED: tuple[tuple[str, str], ...] = (
    # Federal Register API v1 + its full-text document endpoints
    ("www.federalregister.gov", "/api/v1/"),
    ("www.federalregister.gov", "/documents/full_text/"),
    # eCFR REST API + govinfo bulk XML for Title 31 only
    ("www.ecfr.gov", "/api/"),
    ("www.govinfo.gov", "/bulkdata/ECFR/title-31"),
    # OFAC Sanctions List Service (User-Agent header required by the service)
    ("sanctionslistservice.ofac.treas.gov", "/"),
    # GLEIF Golden Copy / concatenated files
    ("www.gleif.org", "/"),
    # OpenSanctions bulk data (CC-BY-NC 4.0 — attribution in DATA_LICENSE.md)
    ("data.opensanctions.org", "/datasets/"),
    # Treasury Fiscal Data API (optional secondary demo)
    ("api.fiscaldata.treasury.gov", "/services/api/fiscal_service/"),
    # Authority, drafting, and governance references (docs/DATA_SOURCES.md):
    # OLRC U.S. Code USLM XML release-point downloads
    ("uscode.house.gov", "/download/"),
    # Document Drafting Handbook (Aug 2018 ed., rev. 2.2)
    ("www.archives.gov", "/files/federal-register/"),
    # E.O. 14192 accounting PDFs (Unified Agenda site)
    ("www.reginfo.gov", "/public/pdf/eo14192/"),
)

# (exact host, exact path) pairs — single-file sources where a prefix match
# would over-grant (e.g. "…Inventory.csv.bak" must be refused).
_ALLOWED_EXACT: tuple[tuple[str, str], ...] = (
    # Treasury AI Use Case Inventory CSV — reference snapshot provenancing
    # the site's OGC-01 framing (docs/DATA_SOURCES.md)
    ("home.treasury.gov", "/system/files/136/Treasury-AI-Use-Case-Inventory.csv"),
)


def is_allowed(url: str) -> bool:
    """Return True iff ``url`` is https on the default port and matches an
    allow-listed (host, path prefix) or (host, exact path) entry.

    Fail-closed: URL parse errors, non-default ports, and dot-segment paths
    return False rather than propagate.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        # Fail-closed: an unparseable URL is refused, not retried or passed.
        return False
    if parts.scheme != "https" or parts.port not in (None, 443):
        return False
    host = parts.hostname or ""
    path = parts.path or "/"
    # Fail-closed: dot segments could re-escape an allow-listed prefix after
    # server-side normalization, so they are refused outright.
    if any(segment in (".", "..") for segment in path.split("/")):
        return False
    if any(host == allowed_host and path == exact for allowed_host, exact in _ALLOWED_EXACT):
        return True
    return any(
        host == allowed_host and path.startswith(prefix) for allowed_host, prefix in _ALLOWED
    )


def require_allowed(url: str) -> str:
    """Return ``url`` unchanged if allow-listed; raise :class:`DisallowedSourceError` otherwise."""
    if not is_allowed(url):
        raise DisallowedSourceError(f"URL not on the docs/DATA_SOURCES.md allow-list: {url}")
    return url
