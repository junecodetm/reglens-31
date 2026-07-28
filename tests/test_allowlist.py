"""Allow-list enforcement: only the six documented sources pass; everything else is refused."""

import pytest

from reglens.ingest.allowlist import DisallowedSourceError, is_allowed, require_allowed

ALLOWED_URLS = [
    "https://www.federalregister.gov/api/v1/documents.json?per_page=1",
    "https://www.federalregister.gov/documents/full_text/text/2026/01/02/some-doc.txt",
    "https://www.ecfr.gov/api/versioner/v1/full/2026-05-07/title-31.xml",
    "https://www.govinfo.gov/bulkdata/ECFR/title-31/ECFR-title31.xml",
    "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN_ADVANCED.XML",
    "https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy",
    "https://data.opensanctions.org/datasets/latest/us_ofac_sdn/entities.ftm.json",
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny",
]

REFUSED_URLS = [
    "https://example.com/anything",
    "http://www.federalregister.gov/api/v1/documents.json",  # non-https refused
    "https://www.govinfo.gov/bulkdata/ECFR/title-26/x.xml",  # wrong CFR title
    "https://api.groq.com/openai/v1/chat/completions",
    "https://www.federalregister.gov.evil.example/api/v1/x",  # host suffix spoof
    "https://boiefiling.fincen.gov/anything",  # excluded by invariant 3
    "not a url",
    "",
]


@pytest.mark.parametrize("url", ALLOWED_URLS)
def test_allowed_sources_pass(url: str) -> None:
    assert is_allowed(url)
    assert require_allowed(url) == url


@pytest.mark.parametrize("url", REFUSED_URLS)
def test_everything_else_is_refused(url: str) -> None:
    assert not is_allowed(url)
    with pytest.raises(DisallowedSourceError):
        require_allowed(url)
