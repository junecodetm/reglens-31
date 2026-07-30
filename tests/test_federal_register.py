"""Federal Register client against respx mocks — zero real network in tests."""

from pathlib import Path

import pytest
import respx
from httpx import Request, Response

from reglens.config import Settings
from reglens.ingest.federal_register import (
    API_BASE,
    corpus_document_numbers,
    ingest_document,
    latest_treasury_rule,
    make_client,
    rules_amending_part,
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


def test_unsafe_document_numbers_are_refused() -> None:
    from reglens.ingest.federal_register import require_safe_document_number

    for bad in ("../etc/passwd", "a/b", "a b", "", "x\n"):
        with pytest.raises(ValueError, match="unsafe document number"):
            require_safe_document_number(bad)
    assert require_safe_document_number("2026-15112") == "2026-15112"


@respx.mock(assert_all_mocked=True)
def test_latest_treasury_rule_returns_document_number(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(url__startswith=f"{API_BASE}/documents.json").mock(
        return_value=Response(200, json={"results": [{"document_number": DOC_NUMBER}]})
    )
    with make_client(Settings()) as client:
        assert latest_treasury_rule(client) == DOC_NUMBER


@respx.mock(assert_all_mocked=True)
def test_rules_amending_part_follows_every_page(respx_mock: respx.MockRouter) -> None:
    """The inclusion rule must not silently stop at the first page of results."""
    pages: dict[str, object] = {
        "1": {"results": [{"document_number": "2026-00001"}], "total_pages": 3},
        "2": {"results": [{"document_number": "2026-00002"}], "total_pages": 3},
        "3": {"results": [{"document_number": "2026-00003"}], "total_pages": 3},
    }

    def by_page(request: Request) -> Response:
        return Response(200, json=pages[request.url.params["page"]])

    respx_mock.get(url__startswith=f"{API_BASE}/documents.json").mock(side_effect=by_page)
    with make_client(Settings()) as client:
        found = rules_amending_part(client, title=31, part=285)
    assert found == ["2026-00001", "2026-00002", "2026-00003"]


@respx.mock(assert_all_mocked=True)
def test_corpus_document_numbers_dedupes_and_sorts(respx_mock: respx.MockRouter) -> None:
    """A rule amending two parts is ingested once; order is deterministic."""
    by_part: dict[str, list[dict[str, str]]] = {
        "285": [{"document_number": "2026-00002"}, {"document_number": "2026-00001"}],
        "356": [{"document_number": "2026-00002"}, {"document_number": "2026-00003"}],
    }

    def by_cfr_part(request: Request) -> Response:
        part = request.url.params["conditions[cfr][part]"]
        return Response(200, json={"results": by_part[part], "total_pages": 1})

    respx_mock.get(url__startswith=f"{API_BASE}/documents.json").mock(side_effect=by_cfr_part)
    with make_client(Settings()) as client:
        found = corpus_document_numbers(client, title=31, parts=(285, 356))
    assert found == ["2026-00001", "2026-00002", "2026-00003"]


@respx.mock(assert_all_mocked=True)
def test_corpus_enumeration_refuses_unsafe_document_numbers(
    respx_mock: respx.MockRouter,
) -> None:
    """Fail-closed: a hostile document number from the remote API never becomes a filename."""
    respx_mock.get(url__startswith=f"{API_BASE}/documents.json").mock(
        return_value=Response(
            200, json={"results": [{"document_number": "../../etc/passwd"}], "total_pages": 1}
        )
    )
    with make_client(Settings()) as client, pytest.raises(ValueError, match="unsafe document"):
        rules_amending_part(client, title=31, part=285)
