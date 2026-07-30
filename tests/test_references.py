"""Pinned reference ingestion rejects unsafe or non-PDF responses."""

from pathlib import Path

import pytest
import respx
from httpx import Request, Response

from reglens.config import Settings
from reglens.ingest import references
from reglens.ingest.allowlist import DisallowedSourceError
from reglens.ingest.snapshot import read_manifest

ALLOWED_PDF_URL = references.REFERENCE_PDFS[0][1]
PDF_BYTES = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


def _pin_reference(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    pins: tuple[tuple[str, str], ...] = (("test-reference", url),)
    monkeypatch.setattr(references, "REFERENCE_PDFS", pins)


@respx.mock(assert_all_mocked=True)
def test_html_response_raises_without_writing_a_snapshot(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _pin_reference(monkeypatch, ALLOWED_PDF_URL)

    def html_response(_request: Request) -> Response:
        return Response(200, content=b"<html>")

    respx_mock.get(ALLOWED_PDF_URL).mock(side_effect=html_response)

    with pytest.raises(ValueError, match="did not return a PDF"):
        references.ingest_references(Settings(data_dir=data_dir))

    assert list(data_dir.iterdir()) == []


@respx.mock(assert_all_mocked=True)
def test_pdf_response_writes_pdf_snapshot_manifest(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_reference(monkeypatch, ALLOWED_PDF_URL)

    def pdf_response(_request: Request) -> Response:
        return Response(200, content=PDF_BYTES)

    respx_mock.get(ALLOWED_PDF_URL).mock(side_effect=pdf_response)

    snapshot_dirs = references.ingest_references(Settings(data_dir=tmp_path))

    assert len(snapshot_dirs) == 1
    snapshot_dir = snapshot_dirs[0]
    manifest = read_manifest(snapshot_dir)
    assert manifest.content_type == "application/pdf"
    assert manifest.filename.endswith(".pdf")
    assert (snapshot_dir / manifest.filename).read_bytes() == PDF_BYTES


@respx.mock(assert_all_mocked=True)
def test_off_allowlist_url_raises_before_any_http_request(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_reference(monkeypatch, "https://example.invalid/reference.pdf")

    with pytest.raises(DisallowedSourceError):
        references.ingest_references(Settings(data_dir=tmp_path))

    assert len(respx_mock.calls) == 0


@respx.mock(assert_all_mocked=True)
def test_redirect_to_an_off_allowlist_host_is_refused(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An allow-listed URL must not be able to redirect the fetch off the allow-list.

    Guards the ``recheck_redirects`` response hook: without it a compromised or
    misconfigured upstream could redirect an approved host to an arbitrary one
    and the payload would be snapshotted as if it were the reference document.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _pin_reference(monkeypatch, ALLOWED_PDF_URL)
    evil_url = "https://evil.invalid/payload.pdf"

    respx_mock.get(ALLOWED_PDF_URL).mock(return_value=Response(302, headers={"Location": evil_url}))

    with pytest.raises(DisallowedSourceError):
        references.ingest_references(Settings(data_dir=data_dir))

    # No route is registered for evil_url, so with assert_all_mocked=True any attempt
    # to actually fetch it fails this test — the hop is refused before it is sent.
    assert list(data_dir.iterdir()) == []


@respx.mock(assert_all_mocked=True)
def test_redirect_within_the_allowlist_is_followed(
    respx_mock: respx.MockRouter,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The redirect guard must reject off-list hops without breaking legitimate ones."""
    _pin_reference(monkeypatch, ALLOWED_PDF_URL)
    same_host_url = "https://www.archives.gov/files/federal-register/write/handbook/ddh-v2.pdf"

    respx_mock.get(ALLOWED_PDF_URL).mock(
        return_value=Response(302, headers={"Location": same_host_url})
    )
    respx_mock.get(same_host_url).mock(return_value=Response(200, content=PDF_BYTES))

    snapshot_dirs = references.ingest_references(Settings(data_dir=tmp_path))

    assert len(snapshot_dirs) == 1
    assert (snapshot_dirs[0] / read_manifest(snapshot_dirs[0]).filename).read_bytes() == PDF_BYTES
