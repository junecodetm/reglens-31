"""PII redaction scrubs identifiers without destroying the log's useful content."""

from pathlib import Path

import pytest

from scripts.redact_pii import main, redact


def test_redacts_each_identifier_class() -> None:
    assert redact("contact ana.perez+tag@example.gov now") == "contact [EMAIL] now"
    assert redact("ssn 123-45-6789 recorded") == "ssn [SSN] recorded"
    assert redact("call (202) 555-0143 today") == "call [PHONE] today"
    assert redact("from 192.168.10.7 ok") == "from [IP] ok"
    # 4111111111111111 is the canonical Luhn-valid test card.
    assert redact("card 4111111111111111 seen") == "card [CARD] seen"


def test_leaves_legitimate_log_content_intact() -> None:
    """Over-redaction would make the logs useless, so precision matters as much as recall."""
    line = (
        "document=2026-15112 sha256=3be0750516f615dc85992c480478a67a "
        "cite=31 CFR 285.5 accepted=950 rejected=163 date=2026-07-30"
    )

    assert redact(line) == line


def test_long_digit_runs_that_are_not_cards_survive() -> None:
    """The Luhn check is what keeps hashes and byte counts out of [CARD]."""
    assert redact("bytes=1234567890123456") == "bytes=1234567890123456"


def test_redaction_is_applied_to_unparseable_lines() -> None:
    """Fail-closed: scrubbing does not depend on the line being valid JSON."""
    assert "[EMAIL]" in redact('{"broken": "ana@example.gov')


def test_check_mode_reports_without_writing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "run.log"
    log.write_text("user ana@example.gov\nplain line\n")

    exit_code = main([str(log), "--check"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "run.log:1" in captured.err
    assert captured.out == ""


def test_check_mode_passes_on_clean_logs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = tmp_path / "clean.log"
    log.write_text("document=2026-15112 accepted=12\n")

    assert main([str(log), "--check"]) == 0
    assert capsys.readouterr().err == ""


def test_file_mode_writes_redacted_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log = tmp_path / "run.log"
    log.write_text("user ana@example.gov\n")

    assert main([str(log)]) == 0
    assert capsys.readouterr().out == "user [EMAIL]\n"
