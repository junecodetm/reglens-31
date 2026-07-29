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


def export_ogc01_data(settings: Settings, web_dir: Path) -> None:
    """Export EXTEND-OGC01 artifacts (authority, grounding, drafts, texts).

    The U.S.C. section texts and derived part texts are written byte-identical
    to what the provenance gate verified, so UI highlight offsets never drift.
    Failure mode: missing pipeline outputs raise ``FileNotFoundError`` — a
    partial export is never produced silently.
    """
    from reglens.authority.records import AuthorityExport
    from reglens.authority.run import AUTHORITY_JSON
    from reglens.draft.run import CONFORMANCE_JSON, DRAFTS_DIR
    from reglens.grounding.run import GROUNDING_JSON
    from reglens.ingest.ecfr import xml_to_text

    out_dir = web_dir / "public" / "data"
    usc_dir = out_dir / "usc"
    parts_dir = out_dir / "authority-parts"
    drafts_out = out_dir / "drafts"
    for directory in (usc_dir, parts_dir, drafts_out):
        directory.mkdir(parents=True, exist_ok=True)

    export = AuthorityExport.model_validate_json(AUTHORITY_JSON.read_text())
    (out_dir / "authority.json").write_text(export.model_dump_json(indent=2) + "\n")
    (out_dir / "grounding.json").write_text(GROUNDING_JSON.read_text())
    (out_dir / "conformance.json").write_text(CONFORMANCE_JSON.read_text())
    for draft_path in sorted(DRAFTS_DIR.glob("*.txt")):
        (drafts_out / draft_path.name).write_bytes(draft_path.read_bytes())

    raw_root = settings.data_dir / "raw"
    for snapshot_dir in sorted(raw_root.iterdir()):
        if not (snapshot_dir / "manifest.json").is_file():
            continue
        manifest = read_manifest(snapshot_dir)
        if manifest.content_type == "text/x-usc-section" and manifest.filename.endswith(".txt"):
            payload = (snapshot_dir / manifest.filename).read_bytes()
            (usc_dir / manifest.filename).write_bytes(payload)
        elif manifest.content_type == "application/xml" and "-authority-" in manifest.filename:
            # Same deterministic derivation as reglens.authority.run — byte-identical.
            text = xml_to_text((snapshot_dir / manifest.filename).read_bytes())
            part_stem = manifest.filename.rsplit("-authority-", 1)[0]
            (parts_dir / f"{part_stem}.txt").write_text(text)


def main() -> int:
    settings = Settings()
    out_dir = export_web_data(settings, Path("web"))
    export_ogc01_data(settings, Path("web"))
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
