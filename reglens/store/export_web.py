"""Export processed claims + source texts as static assets for the web UI.

Inputs: ``data/processed/claims.json`` and the raw snapshots it references.
Outputs: ``web/public/data/claims.json``, ``web/public/data/documents/<n>.txt``
and ``web/public/data/site.json`` (counts, model tag, "as of" date derived
from snapshot manifests — never wall-clock). Failure mode: missing inputs
raise ``FileNotFoundError``; malformed records raise ``ValidationError``; a
non-https document URL is dropped to empty rather than shipped as a link sink.
"""

import json
from pathlib import Path

from reglens.config import Settings
from reglens.extract.records import DocumentExtraction, load_extractions
from reglens.ingest.federal_register import require_safe_document_number
from reglens.ingest.snapshot import read_manifest


def _sanitized(extraction: DocumentExtraction) -> DocumentExtraction:
    """Enforce https on the outbound link; refuse unsafe document numbers."""
    require_safe_document_number(extraction.document_number)
    if extraction.document_url.startswith("https://"):
        return extraction
    claims = [claim.model_copy(update={"document_url": ""}) for claim in extraction.claims]
    return extraction.model_copy(update={"document_url": "", "claims": claims})


def export_web_data(settings: Settings, web_dir: Path) -> Path:
    """Copy claims, per-document text, and site metadata into ``web/public/data``."""
    claims_path = settings.data_dir / "processed" / "claims.json"
    extractions = [_sanitized(extraction) for extraction in load_extractions(claims_path)]

    out_dir = web_dir / "public" / "data"
    documents_dir = out_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    by_sha = {extraction.document_sha256: extraction for extraction in extractions}
    latest_fetch = ""
    for snapshot_dir in sorted((settings.data_dir / "raw").iterdir()):
        if (snapshot_dir / "manifest.json").is_file():
            manifest = read_manifest(snapshot_dir)
            latest_fetch = max(latest_fetch, manifest.fetched_at)
            extraction = by_sha.get(manifest.sha256)
            if manifest.content_type == "text/plain" and extraction is not None:
                source = (snapshot_dir / manifest.filename).read_text()
                (documents_dir / f"{extraction.document_number}.txt").write_text(source)

    model_tags = sorted(
        {claim.run.model_tag for extraction in extractions for claim in extraction.claims}
    )
    accepted = sum(extraction.accepted_count for extraction in extractions)
    rejected = sum(extraction.rejected_count for extraction in extractions)
    payload = [extraction.model_dump() for extraction in extractions]
    (out_dir / "claims.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    site = {
        "accepted_count": accepted,
        "rejected_count": rejected,
        "document_count": len(extractions),
        "model_tags": model_tags,
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
