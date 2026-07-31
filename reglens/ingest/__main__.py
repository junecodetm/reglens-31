"""CLI: ``python -m reglens.ingest`` — snapshot allow-listed sources.

Usage:
    python -m reglens.ingest                      # most recent Treasury final rule
    python -m reglens.ingest 2026-15112 ...       # specific FR document numbers
    python -m reglens.ingest --treasury-rules 20  # N most recent Treasury rules
    python -m reglens.ingest --ecfr 501 515 560   # Title 31 parts, pinned date
    python -m reglens.ingest --inventory          # Treasury AI Use Case Inventory CSV
    python -m reglens.ingest --corpus             # every rule amending the in-scope parts

Prints one snapshot directory per line.
"""

import argparse

from reglens.config import Settings
from reglens.corpus import CFR_PARTS, CFR_TITLE
from reglens.ingest.ecfr import ingest_part
from reglens.ingest.federal_register import (
    corpus_document_numbers,
    ingest_document,
    make_client,
    recent_treasury_rules,
)
from reglens.ingest.inventory import ingest_use_case_inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens.ingest")
    parser.add_argument("documents", nargs="*", help="FR document numbers")
    parser.add_argument("--treasury-rules", type=int, default=0, metavar="N")
    parser.add_argument("--ecfr", type=int, nargs="+", default=[], metavar="PART")
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument(
        "--corpus",
        action="store_true",
        help="every FR final rule amending an in-scope CFR part (reglens.corpus)",
    )
    args = parser.parse_args(argv)

    settings = Settings()
    if args.inventory:
        print(ingest_use_case_inventory(settings))
        if not args.documents and not args.treasury_rules and not args.ecfr and not args.corpus:
            return 0
    document_numbers: list[str] = list(args.documents)
    if args.corpus:
        with make_client(settings) as client:
            document_numbers.extend(
                corpus_document_numbers(client, title=CFR_TITLE, parts=CFR_PARTS)
            )
    if args.treasury_rules:
        with make_client(settings) as client:
            document_numbers.extend(recent_treasury_rules(client, count=args.treasury_rules))
    if not document_numbers and not args.ecfr and not args.corpus:
        with make_client(settings) as client:
            document_numbers = recent_treasury_rules(client, count=1)

    unavailable: list[str] = []
    for document_number in dict.fromkeys(document_numbers):
        try:
            metadata_dir, text_dir = ingest_document(settings, document_number)
        except LookupError:
            # Coverage is recorded, never hidden: a document the Federal Register
            # publishes without raw text cannot be provenance-checked, so it is
            # reported as a gap rather than silently dropped or half-ingested.
            unavailable.append(document_number)
            continue
        print(metadata_dir)
        print(text_dir)
    for part in args.ecfr:
        metadata_dir, text_dir = ingest_part(settings, part)
        print(metadata_dir)
        print(text_dir)
    if unavailable:
        print(f"no raw text available ({len(unavailable)}): {' '.join(unavailable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
