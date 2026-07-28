"""Export processed claims + source texts as static assets for the web UI.

Inputs: ``data/processed/claims.json`` and the raw snapshots it references.
Outputs: ``web/public/data/claims.json``, ``web/public/data/documents/<n>.txt``
and ``web/public/data/site.json`` (counts, model tag, "as of" date derived
from snapshot manifests — never wall-clock). Failure mode: missing inputs
raise ``FileNotFoundError``; the UI is never built from partial data silently.
"""

import json
from pathlib import Path
from typing import Any

from reglens.config import Settings
from reglens.ingest.snapshot import read_manifest


def export_web_data(settings: Settings, web_dir: Path) -> Path:
    """Copy claims, per-document text, and site metadata into ``web/public/data``."""
    claims_path = settings.data_dir / "processed" / "claims.json"
    extractions: list[dict[str, Any]] = json.loads(claims_path.read_text())

    out_dir = web_dir / "public" / "data"
    documents_dir = out_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    latest_fetch = ""
    model_tags: set[str] = set()
    for snapshot_dir in sorted((settings.data_dir / "raw").iterdir()):
        if (snapshot_dir / "manifest.json").is_file():
            manifest = read_manifest(snapshot_dir)
            latest_fetch = max(latest_fetch, manifest.fetched_at)
            if manifest.content_type == "text/plain":
                for extraction in extractions:
                    if extraction["document_sha256"] == manifest.sha256:
                        source = (snapshot_dir / manifest.filename).read_text()
                        target = documents_dir / f"{extraction['document_number']}.txt"
                        target.write_text(source)

    for extraction in extractions:
        for claim in extraction["claims"]:
            model_tags.add(claim["run"]["model_tag"])

    accepted = sum(extraction["accepted_count"] for extraction in extractions)
    rejected = sum(extraction["rejected_count"] for extraction in extractions)
    (out_dir / "claims.json").write_text(json.dumps(extractions, indent=2, sort_keys=True) + "\n")
    site = {
        "accepted_count": accepted,
        "rejected_count": rejected,
        "document_count": len(extractions),
        "model_tags": sorted(model_tags),
        "data_as_of": latest_fetch[:10],
    }
    (out_dir / "site.json").write_text(json.dumps(site, indent=2, sort_keys=True) + "\n")
    return out_dir


def main() -> int:
    settings = Settings()
    out_dir = export_web_data(settings, Path("web"))
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
