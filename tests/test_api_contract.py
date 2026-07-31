"""The published read API is the site's own data, validated and navigable.

An API is a promise about shape. These tests hold the materialized files to the
models that describe them, check that every link in the service index resolves
to a file that exists, and prove the paginated claim chain reassembles into
exactly the claim set the site renders — so "the API serves what the pages show"
is checked rather than asserted. The byte-identical re-export is what lets CI
diff the tree as a replay guard.
"""

import json
import shutil
from pathlib import Path

import pytest

from reglens.api.schemas import (
    API_VERSION,
    ClaimPage,
    Currency,
    DocumentCollection,
    DocumentDetail,
    Metrics,
    SectionCollection,
    ServiceIndex,
)
from reglens.api.spec import build_openapi
from reglens.store.export_api import export_api_data

SITE_DATA = Path("web") / "public" / "data"


@pytest.fixture(scope="module")
def api_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Export the API from a copy of the committed site data."""
    web_dir = tmp_path_factory.mktemp("web")
    shutil.copytree(SITE_DATA, web_dir / "public" / "data")
    return export_api_data(web_dir)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def test_the_service_index_validates_and_every_link_resolves(api_dir: Path) -> None:
    index = ServiceIndex.model_validate(_load(api_dir / "index.json"))

    assert index.disclaimer, "the non-affiliation disclaimer travels with the data"
    for relation, link in index.links.items():
        assert link.startswith(f"/api/{API_VERSION}/"), relation
        target = api_dir / link.removeprefix(f"/api/{API_VERSION}/")
        assert target.is_file(), f"link '{relation}' points at a file that was not written"


def test_the_index_reports_the_sample_against_the_full_corpus(api_dir: Path) -> None:
    """The disclosure the whole pass exists for, served as data rather than prose."""
    index = ServiceIndex.model_validate(_load(api_dir / "index.json"))

    assert index.corpus.documents_extracted < index.corpus.documents_in_scope
    assert index.corpus.chars_extracted <= index.corpus.chars_in_scope
    assert index.corpus.documents_extracted > 0


def test_document_detail_exists_for_every_document_in_the_collection(api_dir: Path) -> None:
    collection = DocumentCollection.model_validate(_load(api_dir / "documents.json"))

    assert collection.count == len(collection.documents)
    for summary in collection.documents:
        detail = DocumentDetail.model_validate(
            _load(api_dir / "documents" / f"{summary.document_number}.json")
        )
        assert detail.document_sha256 == summary.document_sha256
        assert len(detail.claims) == summary.accepted_count + summary.rejected_count


def test_the_page_chain_reassembles_into_exactly_the_sites_claim_set(api_dir: Path) -> None:
    site_claims = {
        claim["claim_id"]
        for document in json.loads((SITE_DATA / "claims.json").read_text())
        for claim in document["claims"]
    }

    collected: set[str] = set()
    visited = 0
    path: str | None = f"/api/{API_VERSION}/claims/page-1.json"
    while path is not None:
        page = ClaimPage.model_validate(_load(api_dir / path.removeprefix(f"/api/{API_VERSION}/")))
        collected.update(claim.claim_id for claim in page.claims)
        visited += 1
        assert page.page == visited
        path = page.next

    assert visited == ClaimPage.model_validate(_load(api_dir / "claims" / "page-1.json")).page_count
    assert collected == site_claims


def test_first_claim_page_carries_complete_run_metadata(api_dir: Path) -> None:
    """Validate run metadata on the first materialized claim page."""
    page = ClaimPage.model_validate(_load(api_dir / "claims" / "page-1.json"))

    for claim in page.claims:
        assert claim.run.model_tag and claim.run.prompt_sha256 and claim.run.input_sha256
        assert claim.run.chunk_plan_sha256
        assert claim.run.temperature == 0.0
        assert claim.accepted == (claim.start is not None)


def test_metrics_keep_the_provisional_label_attached_to_the_numbers(api_dir: Path) -> None:
    metrics = Metrics.model_validate(_load(api_dir / "metrics.json"))

    assert metrics.provisional_label, "numbers must never be served without their label"
    assert 0.0 <= metrics.f1 <= 1.0
    assert metrics.adjudicated_count <= metrics.total_gold_count


def test_currency_and_sections_validate(api_dir: Path) -> None:
    currency = Currency.model_validate(_load(api_dir / "currency.json"))
    sections = SectionCollection.model_validate(_load(api_dir / "sections.json"))

    assert currency.total_sections == sum(part.census_count for part in currency.parts)
    assert currency.source_urls and all(url.startswith("https://") for url in currency.source_urls)
    assert sections.count == len(sections.sections)


def test_the_openapi_document_describes_every_materialized_endpoint(api_dir: Path) -> None:
    document = json.loads((api_dir / "openapi.json").read_text())

    assert document["openapi"].startswith("3.1")
    for path, operations in document["paths"].items():
        schema = operations["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        name = schema["$ref"].rsplit("/", 1)[-1]
        assert name in document["components"]["schemas"], path


def test_re_exporting_is_byte_identical(tmp_path: Path) -> None:
    """Determinism: the replay guard in CI diffs this tree, so it must not churn."""
    web_dir = tmp_path / "web"
    shutil.copytree(SITE_DATA, web_dir / "public" / "data")

    first = {
        path.relative_to(web_dir): path.read_bytes()
        for path in sorted(export_api_data(web_dir).rglob("*.json"))
    }
    second = {
        path.relative_to(web_dir): path.read_bytes()
        for path in sorted(export_api_data(web_dir).rglob("*.json"))
    }

    assert first == second


def test_the_spec_is_generated_rather_than_stored(api_dir: Path) -> None:
    """A hand-maintained spec drifts; this one is derived from the models."""
    assert json.loads((api_dir / "openapi.json").read_text()) == json.loads(
        json.dumps(build_openapi(), sort_keys=True)
    )
