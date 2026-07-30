"""CLI: ``python -m reglens.extract`` — run extraction + gate over all snapshots."""

import argparse

from reglens.config import Settings
from reglens.extract.llm import OllamaProvider
from reglens.extract.run import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-extract every document, ignoring previously persisted results",
    )
    args = parser.parse_args()
    settings = Settings()
    extractions = run_pipeline(settings, OllamaProvider(settings), force=args.force)
    for extraction in extractions:
        print(
            f"{extraction.document_number}: "
            f"{extraction.accepted_count} accepted, {extraction.rejected_count} rejected"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
