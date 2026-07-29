"""Stage 3 pipeline: skeleton generation → gates → conformance.json.

Inputs: ``data/processed/authority.json`` (Stage 1 output) and the part
text/U.S.C. section snapshots. Outputs: accepted drafts under
``data/processed/drafts/`` plus ``data/processed/conformance.json``.
Failure mode: a draft failing ANY conformance check is rejected — recorded
with its failing checks, never written out with a caveat (fail-closed,
EXTEND-OGC01 Stage 3.4).
"""

from pathlib import Path

from pydantic import BaseModel, Field

from reglens.authority.records import AuthorityExport, PartAuthority
from reglens.config import Settings
from reglens.draft.conformance import DraftChecklist, check_draft
from reglens.draft.narrative import generate_narrative
from reglens.draft.templates import build_skeleton
from reglens.ingest.snapshot import read_manifest

AUTHORITY_JSON = Path("data/processed/authority.json")
DRAFTS_DIR = Path("data/processed/drafts")
CONFORMANCE_JSON = Path("data/processed/conformance.json")

# One NPRM per in-scope part, plus one final-rule variant to exercise both
# templates (part 223 is the smallest part).
FINAL_RULE_PARTS = (223,)


class ConformanceReport(BaseModel):
    """Checklist results + pass rate across every generated draft."""

    checklists: list[DraftChecklist]
    generated: int
    accepted: int
    rejected: int
    pass_rate: float
    total_unverified_quotes: int
    model_note: str = (
        "SUMMARY and SUPPLEMENTARY INFORMATION opening text are model-generated "
        "(pinned local model, temperature 0) and labeled in each draft. All other "
        "content is deterministic template structure, gate-verified set-out text, "
        "or a visible placeholder."
    )
    rejected_drafts: list[str] = Field(default_factory=list[str])


def _verification_corpus(settings: Settings, record: PartAuthority) -> list[str]:
    """Sources a draft's quotes/set-out text may verify against."""
    corpus = [record.authority_text]
    stem = f"31-CFR-{record.part}-authority-{record.ecfr_date}"
    raw_root = settings.data_dir / "raw"
    for snapshot_dir in sorted(raw_root.iterdir()):
        if not (snapshot_dir / "manifest.json").is_file():
            continue
        manifest = read_manifest(snapshot_dir)
        if manifest.filename == f"{stem}.txt" or (
            manifest.content_type == "text/x-usc-section" and manifest.filename.endswith(".txt")
        ):
            corpus.append((snapshot_dir / manifest.filename).read_text())
    return corpus


def build_drafts(settings: Settings) -> ConformanceReport:
    """Generate, gate, and persist every draft; write the conformance report."""
    export = AuthorityExport.model_validate_json(AUTHORITY_JSON.read_text())
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    checklists: list[DraftChecklist] = []
    rejected_names: list[str] = []
    for record in export.parts:
        doc_types = ["nprm"] + (["final"] if record.part in FINAL_RULE_PARTS else [])
        corpus = _verification_corpus(settings, record)
        for doc_type in doc_types:
            narrative = generate_narrative(
                settings,
                record.part,
                record.part_heading,
                record.authority_text,
                doc_type,
            )
            narrative_text = f"{narrative.summary}\n{narrative.supplementary_intro}"
            draft = build_skeleton(
                record, doc_type, narrative.summary, narrative.supplementary_intro
            )
            checklist = check_draft(record.part, doc_type, draft, narrative_text, corpus)
            checklists.append(checklist)
            name = f"31-CFR-{record.part}-{doc_type}.txt"
            if checklist.passed:
                (DRAFTS_DIR / name).write_text(draft)
            else:
                # Fail-closed: rejected drafts are never written out; any
                # stale accepted copy from a prior run is removed.
                (DRAFTS_DIR / name).unlink(missing_ok=True)
                rejected_names.append(name)
    accepted = sum(1 for checklist in checklists if checklist.passed)
    report = ConformanceReport(
        checklists=checklists,
        generated=len(checklists),
        accepted=accepted,
        rejected=len(checklists) - accepted,
        pass_rate=accepted / len(checklists) if checklists else 0.0,
        total_unverified_quotes=sum(c.unverified_quote_count for c in checklists),
        rejected_drafts=rejected_names,
    )
    CONFORMANCE_JSON.write_text(report.model_dump_json(indent=2) + "\n")
    return report


def main() -> int:
    report = build_drafts(Settings())
    print(
        f"drafts: {report.accepted}/{report.generated} accepted "
        f"(pass rate {report.pass_rate:.2f}), "
        f"{report.total_unverified_quotes} unverified quotes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
