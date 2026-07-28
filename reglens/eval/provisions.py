"""Deterministic provision sampling for the gold set (docs/EVALUATION.md).

Inputs: discovered document pairs. Outputs: a seeded, stratified sample of
paragraph-level provisions written to ``reglens/eval/gold/provisions.jsonl``.
Failure mode: documents with no qualifying paragraphs contribute nothing; the
sampler never fabricates spans — every provision is a verbatim slice with
recorded offsets.
"""

import hashlib
import json
import random
from pathlib import Path

from pydantic import BaseModel

from reglens.extract.run import DocumentPair, discover_documents

MIN_CHARS = 100
MAX_CHARS = 1500


class Provision(BaseModel):
    """One candidate provision: a verbatim slice of a source document."""

    provision_id: str
    document_number: str
    document_sha256: str
    start: int
    end: int
    text: str


def candidate_paragraphs(pair: DocumentPair) -> list[tuple[int, int]]:
    """Offsets of paragraphs within the size band, in document order."""
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for paragraph in pair.text.split("\n\n"):
        stripped = paragraph.strip()
        if MIN_CHARS <= len(stripped) <= MAX_CHARS:
            start = pair.text.index(paragraph, cursor) + (len(paragraph) - len(paragraph.lstrip()))
            offsets.append((start, start + len(stripped)))
        cursor += len(paragraph) + 2
    return offsets


def sample_provisions(
    pairs: list[DocumentPair], per_document: int = 7, seed: int = 31
) -> list[Provision]:
    """Seeded stratified sample: up to ``per_document`` provisions from every document."""
    rng = random.Random(seed)
    provisions: list[Provision] = []
    for pair in pairs:
        offsets = candidate_paragraphs(pair)
        chosen = sorted(rng.sample(offsets, min(per_document, len(offsets))))
        for start, end in chosen:
            digest = hashlib.sha256(f"{pair.text_sha256}\x00{start}\x00{end}".encode())
            provisions.append(
                Provision(
                    provision_id=digest.hexdigest()[:16],
                    document_number=pair.document_number,
                    document_sha256=pair.text_sha256,
                    start=start,
                    end=end,
                    text=pair.text[start:end],
                )
            )
    return provisions


def main(argv: list[str] | None = None) -> int:
    import argparse

    from reglens.config import Settings

    parser = argparse.ArgumentParser(prog="reglens.eval.provisions")
    parser.add_argument(
        "--supplement-ecfr",
        action="store_true",
        help="append a second stratum sampled from operative eCFR parts only",
    )
    args = parser.parse_args(argv)

    settings = Settings()
    pairs = discover_documents(settings.data_dir)
    out_path = Path("reglens/eval/gold/provisions.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.supplement_ecfr:
        # Stratum 2 (disclosed in the data card): operative regulatory text is
        # obligation-dense; the base FR-heavy sample under-represents positives.
        existing_ids = {
            json.loads(line)["provision_id"]
            for line in out_path.read_text().splitlines()
            if line.strip()
        }
        ecfr_pairs = [pair for pair in pairs if pair.document_number.startswith("31-CFR")]
        supplement = [
            provision
            for provision in sample_provisions(ecfr_pairs, per_document=25, seed=32)
            if provision.provision_id not in existing_ids
        ]
        with out_path.open("a") as handle:
            for provision in supplement:
                handle.write(json.dumps(provision.model_dump(), sort_keys=True) + "\n")
        print(f"+{len(supplement)} eCFR provisions appended -> {out_path}")
        return 0

    provisions = sample_provisions(pairs)
    lines = [json.dumps(provision.model_dump(), sort_keys=True) for provision in provisions]
    out_path.write_text("\n".join(lines) + "\n")
    print(f"{len(provisions)} provisions -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
