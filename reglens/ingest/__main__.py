"""CLI: ``python -m reglens.ingest [document_number ...]``.

With no arguments, ingests the most recent Treasury final rule from the
Federal Register. Prints one snapshot directory per line.
"""

import sys

from reglens.config import Settings
from reglens.ingest.federal_register import ingest_document, latest_treasury_rule, make_client


def main(argv: list[str]) -> int:
    settings = Settings()
    document_numbers = argv or None
    if document_numbers is None:
        with make_client(settings) as client:
            document_numbers = [latest_treasury_rule(client)]
    for document_number in document_numbers:
        metadata_dir, text_dir = ingest_document(settings, document_number)
        print(metadata_dir)
        print(text_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
