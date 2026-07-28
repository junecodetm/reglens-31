"""Federal Register client against respx mocks — zero real network in tests."""

from pathlib import Path

import respx
from httpx import Response

from reglens.config import Settings
from reglens.ingest.federal_register import (
    API_BASE,
    ingest_document,
    latest_treasury_rule,
    make_client,
)
from reglens.ingest.snapshot import read_manifest

DOC_NUMBER = "2026-01234"
RAW_TEXT_URL = (
    f"https://www.federalregister.gov/documents/full_text/text/2026/07/01/{DOC_NUMBER}.txt"
)

METADATA = {
    "document_number": DOC_NUMBER,
    "title": "Sample Treasury Final Rule",
    "publication_date": "2026-07-01",
    "html_url": f"https://www.federalregister.gov/documents/2026/07/01/{DOC_NUMBER}/sample",
    "raw_text_url": RAW_TEXT_URL,
    "unknown_upstream_field": "tolerated",
}


@respx.mock(assert_all_mocked=True)
def test_ingest_document_snapshots_metadata_and_text(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    respx_mock.get(f"{API_BASE}/documents/{DOC_NUMBER}.json").mock(
        return_value=Response(200, json=METADATA)
    )
    respx_mock.get(RAW_TEXT_URL).mock(return_value=Response(200, text="Each person must file."))

    settings = Settings(data_dir=tmp_path)
    metadata_dir, text_dir = ingest_document(settings, DOC_NUMBER)

    assert read_manifest(metadata_dir).source_id == "federal_register"
    assert (text_dir / f"{DOC_NUMBER}.txt").read_text() == "Each person must file."


@respx.mock(assert_all_mocked=True)
def test_latest_treasury_rule_returns_document_number(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(url__startswith=f"{API_BASE}/documents.json").mock(
        return_value=Response(200, json={"results": [{"document_number": DOC_NUMBER}]})
    )
    with make_client(Settings()) as client:
        assert latest_treasury_rule(client) == DOC_NUMBER
