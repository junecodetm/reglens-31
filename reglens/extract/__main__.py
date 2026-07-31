"""CLI: ``python -m reglens.extract`` — extract + gate the sampled documents.

Defaults to the extraction sample stated in :mod:`reglens.corpus`. ``--all``
extracts every in-scope document instead, which is hours of local inference.
"""

import argparse

from reglens.config import Settings
from reglens.extract.llm import OllamaProvider
from reglens.extract.run import discover_documents, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-extract the selected documents, ignoring previously persisted results",
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--documents",
        metavar="NUMBER",
        nargs="+",
        help=(
            "restrict inference to these document numbers (e.g. 31-CFR-501); every "
            "other already-extracted document is carried forward with its original "
            "run record intact"
        ),
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help=(
            "extract every committed document rather than the stated sample "
            "(reglens.corpus.in_extraction_sample) — hours of local inference. "
            "The committed artifact is the sample, so a later bare run narrows "
            "back to it; committing a full-corpus result means updating the "
            "pinned expectations in tests/test_corpus.py"
        ),
    )
    args = parser.parse_args()
    settings = Settings()
    documents = None
    if args.documents:
        documents = frozenset(args.documents)
    elif args.all:
        documents = frozenset(
            pair.document_number for pair in discover_documents(settings.data_dir)
        )
    extractions = run_pipeline(
        settings,
        OllamaProvider(settings),
        force=args.force,
        documents=documents,
    )
    for extraction in extractions:
        print(
            f"{extraction.document_number}: "
            f"{extraction.accepted_count} accepted, {extraction.rejected_count} rejected"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
