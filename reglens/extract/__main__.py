"""CLI: ``python -m reglens.extract`` — run extraction + gate over all snapshots."""

from reglens.config import Settings
from reglens.extract.llm import OllamaProvider
from reglens.extract.run import run_pipeline


def main() -> int:
    settings = Settings()
    extractions = run_pipeline(settings, OllamaProvider(settings))
    for extraction in extractions:
        print(
            f"{extraction.document_number}: "
            f"{extraction.accepted_count} accepted, {extraction.rejected_count} rejected"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
