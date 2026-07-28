"""Gold-set record contract: machine-proposed until a human adjudicates."""

import json
from pathlib import Path

from pydantic import BaseModel

from reglens.eval.provisions import Provision


class GoldRecord(BaseModel):
    """One provision-level label. ``adjudicated`` is False until a human rules on it."""

    provision_id: str
    is_obligation: bool
    obligation_type: str | None = None
    affected_party: str | None = None
    effective_date: str | None = None
    rationale: str = ""
    proposed_by: str
    adjudicated: bool = False


def load_jsonl(path: Path) -> list[GoldRecord]:
    """Validated gold records; raises on malformed lines (bad labels never pass silently)."""
    return [
        GoldRecord.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_provisions(path: Path) -> dict[str, Provision]:
    """Provisions keyed by id."""
    return {
        provision.provision_id: provision
        for provision in (
            Provision.model_validate_json(line)
            for line in path.read_text().splitlines()
            if line.strip()
        )
    }


def merge_batches(batch_dir: Path, out_path: Path) -> int:
    """Concatenate per-batch proposal files into one validated JSONL; returns record count.

    Failure mode: duplicate provision ids raise ``ValueError`` — a double-labeled
    provision is a protocol violation, not something to average away.
    """
    records: list[GoldRecord] = []
    seen: set[str] = set()
    for batch_path in sorted(batch_dir.glob("batch_*.jsonl")):
        for record in load_jsonl(batch_path):
            if record.provision_id in seen:
                raise ValueError(f"duplicate proposal for provision {record.provision_id}")
            seen.add(record.provision_id)
            records.append(record)
    out_path.write_text(
        "\n".join(json.dumps(record.model_dump(), sort_keys=True) for record in records) + "\n"
    )
    return len(records)
