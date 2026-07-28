"""eCFR ingest against respx mocks — XML flattens to text, snapshots are paired."""

from pathlib import Path

import respx
from httpx import Response

from reglens.config import Settings
from reglens.ingest.ecfr import ingest_part, part_url, xml_to_text

PART_XML = (
    b'<?xml version="1.0"?><DIV5 N="501" TYPE="PART">'
    b"<HEAD>PART 501 - REPORTING, PROCEDURES AND PENALTIES REGULATIONS</HEAD>"
    b'<DIV8 N="501.601" TYPE="SECTION"><HEAD>Sec. 501.601 Records and recordkeeping.</HEAD>'
    b"<P>Every person engaging in any transaction subject to this chapter shall keep a full "
    b"record of each such transaction for at least 5 years.</P></DIV8></DIV5>"
)


def test_xml_to_text_flattens_and_keeps_obligation_language() -> None:
    text = xml_to_text(PART_XML)
    assert "shall keep a full record" in text
    assert "<" not in text


@respx.mock(assert_all_mocked=True)
def test_ingest_part_snapshots_metadata_and_text(
    respx_mock: respx.MockRouter, tmp_path: Path
) -> None:
    settings = Settings(data_dir=tmp_path)
    respx_mock.get(part_url(settings.ecfr_date, 501)).mock(
        return_value=Response(200, content=PART_XML)
    )
    metadata_dir, text_dir = ingest_part(settings, 501)
    assert (metadata_dir / "31-CFR-501.json").is_file()
    assert "shall keep a full record" in (text_dir / "31-CFR-501.txt").read_text()
