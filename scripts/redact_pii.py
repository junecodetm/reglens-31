"""Redact personal identifiers from log output before it is stored or shared.

Inputs: log text on stdin, or paths given as arguments. Outputs: the same text
with personal identifiers replaced by typed placeholders such as ``[EMAIL]``.
Failure mode: fail-closed by construction — redaction is applied to the raw
bytes of every line regardless of whether the line parses as structured JSON, so
a malformed or unexpected log record is scrubbed rather than passed through.

RegLens-31 ingests only public U.S. government sources and never ingests private
individual PII (CLAUDE.md section 2, invariant 3), so this is defense in depth:
it protects against an identifier reaching a log by way of an operator's shell,
an exception message, or a future source that has not been vetted.

Usage:
    python scripts/redact_pii.py < run.log > run.redacted.log
    python scripts/redact_pii.py run.log other.log --check
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

# Ordered: earlier patterns win, so a match cannot be re-scanned by a later,
# broader rule. Each is deliberately narrow to keep logs useful — over-redacting
# document numbers such as "2026-01234" would defeat the point of having logs.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("[EMAIL]", re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
    ("[SSN]", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    (
        "[PHONE]",
        re.compile(r"(?<![\w-])(?:\+1[-. ]?)?(?:\(\d{3}\)|\d{3})[-. ]\d{3}[-. ]\d{4}(?![\w-])"),
    ),
    ("[IP]", re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")),
)

_CARD_CANDIDATE = re.compile(r"(?<![\w-])(?:\d[ -]?){12,18}\d(?![\w-])")


def _luhn_ok(digits: str) -> bool:
    """Luhn checksum, used so only plausible card numbers are redacted.

    Without it, any long digit run — a SHA prefix, a byte count — would be
    redacted and the logs would lose the identifiers they exist to carry.
    """
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _redact_cards(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group())
        return "[CARD]" if 13 <= len(digits) <= 19 and _luhn_ok(digits) else match.group()

    return _CARD_CANDIDATE.sub(replace, text)


def redact(text: str) -> str:
    """Replace every recognised personal identifier in ``text`` with a placeholder."""
    for placeholder, pattern in _PATTERNS:
        text = pattern.sub(placeholder, text)
    return _redact_cards(text)


def redact_stream(lines: Iterable[str]) -> Iterable[str]:
    """Redact each line lazily so arbitrarily large logs stream in constant memory."""
    for line in lines:
        yield redact(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="redact_pii", description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="log files (default: stdin)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any identifier is found; write nothing (for CI)",
    )
    args = parser.parse_args(argv)

    sources: list[tuple[str, Iterable[str]]] = (
        [(str(path), path.read_text().splitlines(keepends=True)) for path in args.paths]
        if args.paths
        else [("<stdin>", sys.stdin)]
    )

    found = False
    for name, lines in sources:
        for number, line in enumerate(lines, start=1):
            cleaned = redact(line)
            if cleaned != line:
                found = True
                if args.check:
                    print(f"{name}:{number}: personal identifier found", file=sys.stderr)
            if not args.check:
                sys.stdout.write(cleaned)
    return 1 if (args.check and found) else 0


if __name__ == "__main__":
    raise SystemExit(main())
