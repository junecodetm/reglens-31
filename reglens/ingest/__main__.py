"""CLI: ``python -m reglens.ingest`` — snapshot allow-listed sources.

Usage:
    python -m reglens.ingest                      # most recent Treasury final rule
    python -m reglens.ingest 2026-15112 ...       # specific FR document numbers
    python -m reglens.ingest --treasury-rules 20  # N most recent Treasury rules
    python -m reglens.ingest --ecfr 501 515 560   # Title 31 parts, pinned date

Prints one snapshot directory per line.
"""

import argparse

from reglens.config import Settings
from reglens.ingest.ecfr import ingest_part
from reglens.ingest.federal_register import ingest_document, make_client, recent_treasury_rules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens.ingest")
    parser.add_argument("documents", nargs="*", help="FR document numbers")
    parser.add_argument("--treasury-rules", type=int, default=0, metavar="N")
    parser.add_argument("--ecfr", type=int, nargs="+", default=[], metavar="PART")
    args = parser.parse_args(argv)

    settings = Settings()
    document_numbers: list[str] = list(args.documents)
    if args.treasury_rules:
        with make_client(settings) as client:
            document_numbers.extend(recent_treasury_rules(client, count=args.treasury_rules))
    if not document_numbers and not args.ecfr:
        with make_client(settings) as client:
            document_numbers = recent_treasury_rules(client, count=1)

    for document_number in dict.fromkeys(document_numbers):
        metadata_dir, text_dir = ingest_document(settings, document_number)
        print(metadata_dir)
        print(text_dir)
    for part in args.ecfr:
        metadata_dir, text_dir = ingest_part(settings, part)
        print(metadata_dir)
        print(text_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
