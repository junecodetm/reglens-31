"""Stage 3 pipeline: skeleton generation → gates → conformance.json.

Inputs: ``data/processed/authority.json`` (Stage 1 output) and the part
text/U.S.C. section snapshots. Outputs: accepted drafts under
``data/processed/drafts/`` plus ``data/processed/conformance.json`` with a
per-draft replay dossier.
Failure mode: a draft failing ANY conformance check is rejected — recorded
with its failing checks, never written out with a caveat (fail-closed,
EXTEND-OGC01 Stage 3.4).
"""

import hashlib
from pathlib import Path

from pydantic import BaseModel, Field

from reglens.authority.records import AuthorityExport, PartAuthority
from reglens.config import Settings
from reglens.draft.conformance import DraftChecklist, DraftDossier, check_draft
from reglens.draft.narrative import (
    NARRATIVE_FIELDS,
    NUM_CTX,
    NUM_PREDICT,
    SEED,
    SYSTEM_PROMPT,
    TEMPERATURE,
    generate_narrative,
    render_user_prompt,
)
from reglens.draft.templates import build_skeleton
from reglens.ingest.snapshot import iter_snapshots, read_manifest

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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _part_text(settings: Settings, record: PartAuthority) -> str:
    """Load the flattened source CFR part used to derive narrative inputs.

    Inputs are the data root and authority record; output is the exact
    snapshotted text. Missing or inconsistent provenance raises, so dossier
    generation fails closed instead of hashing an unrelated file.
    """
    snapshot_dir = settings.data_dir / "raw" / record.part_text_sha256
    manifest = read_manifest(snapshot_dir)
    if manifest.sha256 != record.part_text_sha256:
        # Fail-closed: the content address and recorded source must agree.
        raise ValueError(f"part {record.part} snapshot manifest digest mismatch")
    return (snapshot_dir / manifest.filename).read_bytes().decode("utf-8")


def _build_dossier(
    settings: Settings,
    record: PartAuthority,
    doc_type: str,
    part_text: str,
) -> DraftDossier:
    """Build deterministic replay metadata for one generated draft.

    Inputs mirror the model request plus its full source part text; output is
    a typed dossier. Any source-digest mismatch raises before generation, so
    the exported provenance cannot silently describe different input bytes.
    """
    input_sha256 = _sha256_text(part_text)
    if input_sha256 != record.part_text_sha256:
        # Fail-closed: never emit a dossier for text other than the recorded part.
        raise ValueError(f"part {record.part} source text digest mismatch")
    # One model request produces both fields, so the ordered concatenation of
    # actual user prompts currently contains exactly this one shared message.
    user_prompts = (
        render_user_prompt(
            record.part,
            record.part_heading,
            record.authority_text,
            doc_type,
        ),
    )
    return DraftDossier(
        model=settings.model_tag,
        temperature=TEMPERATURE,
        seed=SEED,
        num_ctx=NUM_CTX,
        num_predict=NUM_PREDICT,
        system_prompt_sha256=_sha256_text(SYSTEM_PROMPT),
        prompt_sha256=_sha256_text("".join(user_prompts)),
        input_sha256=input_sha256,
        narrative_fields=list(NARRATIVE_FIELDS),
    )


# Public alias for tests (repo pattern: tests never import private names).
build_dossier = _build_dossier


def _verification_corpus(settings: Settings, record: PartAuthority) -> list[str]:
    """Sources a draft's quotes/set-out text may verify against.

    Scoped to THIS part: its authority line, its part text, and only the
    U.S.C. sections its own authority cites — a quote must never verify
    against a statute cited by a different part.
    """
    corpus = [record.authority_text]
    stem = f"31-CFR-{record.part}-authority-{record.ecfr_date}"
    own_sections = {
        f"usc-{resolved.usc_title}-s{resolved.usc_section}.txt" for resolved in record.resolved
    }
    for snapshot_dir, manifest in iter_snapshots(settings.data_dir / "raw"):
        if manifest.filename == f"{stem}.txt" or (
            manifest.content_type == "text/x-usc-section" and manifest.filename in own_sections
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
        part_text = _part_text(settings, record)
        corpus = _verification_corpus(settings, record)
        for doc_type in doc_types:
            dossier = _build_dossier(settings, record, doc_type, part_text)
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
            checklist = check_draft(
                record.part,
                doc_type,
                draft,
                narrative_text,
                corpus,
                dossier=dossier,
            )
            checklists.append(checklist)
            name = f"31-CFR-{record.part}-{doc_type}.txt"
            if checklist.passed:
                (DRAFTS_DIR / name).write_text(draft, encoding="utf-8", newline="\n")
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
