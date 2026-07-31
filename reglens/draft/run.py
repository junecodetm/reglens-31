"""Drafting pipeline: skeleton generation → gates → conformance.json.

Inputs: ``data/processed/authority.json`` and the part
text/U.S.C. section snapshots. Outputs: accepted drafts under
``data/processed/drafts/`` plus ``data/processed/conformance.json`` with a
per-draft replay dossier.
Failure mode: a draft failing ANY conformance check is rejected — recorded
with its failing checks and never written out with a caveat (fail-closed).
"""

import hashlib
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from reglens.authority.records import AuthorityExport, PartAuthority
from reglens.config import Settings
from reglens.draft.conformance import DraftChecklist, DraftDossier, check_draft
from reglens.draft.narrative import (
    GROQ_MAX_TOKENS,
    GROQ_REASONING_EFFORT,
    NARRATIVE_FIELDS,
    NUM_CTX,
    NUM_PREDICT,
    SEED,
    SYSTEM_PROMPT,
    TEMPERATURE,
    generate_narrative,
    render_user_prompt,
)
from reglens.draft.templates import DOC_TYPES, build_skeleton
from reglens.ingest.snapshot import iter_snapshots, read_manifest

AUTHORITY_JSON = Path("data/processed/authority.json")
DRAFTS_DIR = Path("data/processed/drafts")
CONFORMANCE_JSON = Path("data/processed/conformance.json")


class ConformanceReport(BaseModel):
    """Checklist results + pass rate across every generated draft."""

    checklists: list[DraftChecklist]
    generated: int
    accepted: int
    rejected: int
    pass_rate: float
    total_unverified_quotes: int
    model_note: str = ""
    rejected_drafts: list[str] = Field(default_factory=list[str])


def _model_note(checklists: list[DraftChecklist]) -> str:
    """State exactly which pinned model(s) produced the narrative fields."""
    tags = sorted({f"{c.dossier.provider}:{c.dossier.model}" for c in checklists})
    return (
        "SUMMARY and SUPPLEMENTARY INFORMATION opening text are model-generated "
        f"(pinned model {', '.join(tags)} at temperature 0) and labeled in each "
        "draft. All other content is deterministic template structure, "
        "gate-verified set-out text, or a visible placeholder."
    )


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
    hosted = settings.draft_provider == "groq"
    return DraftDossier(
        provider=settings.draft_provider,
        model=settings.groq_model_tag if hosted else settings.model_tag,
        temperature=TEMPERATURE,
        seed=SEED,
        num_ctx=None if hosted else NUM_CTX,
        num_predict=None if hosted else NUM_PREDICT,
        max_tokens=GROQ_MAX_TOKENS if hosted else None,
        reasoning_effort=GROQ_REASONING_EFFORT if hosted else None,
        system_prompt_sha256=_sha256_text(SYSTEM_PROMPT),
        prompt_sha256=_sha256_text("".join(user_prompts)),
        input_sha256=input_sha256,
        narrative_fields=list(NARRATIVE_FIELDS),
    )


# Public aliases for tests (repo pattern: tests never import private names).
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


def _reusable_checklist(
    previous: ConformanceReport | None,
    dossier: DraftDossier,
    part: int,
    doc_type: str,
) -> DraftChecklist | None:
    """A prior checklist whose dossier matches the run we would perform now.

    Mirrors extraction's document-level reuse: any change to provider, model,
    prompt, generation knobs, or source part text changes the dossier and
    invalidates the record — so ``just rebuild`` after an unrelated stage is a
    no-op that needs no network, while a real input change regenerates.
    Failure mode: a matching *passed* record whose draft artifact is missing
    returns ``None`` (regenerate) rather than trusting an absent file.
    """
    if previous is None:
        return None
    for checklist in previous.checklists:
        if (
            checklist.part == part
            and checklist.doc_type == doc_type
            and checklist.dossier == dossier
        ):
            name = f"31-CFR-{part}-{doc_type}.txt"
            if checklist.passed and not (DRAFTS_DIR / name).is_file():
                return None
            return checklist
    return None


reusable_checklist = _reusable_checklist


def _previous_report() -> ConformanceReport | None:
    """The last persisted report, or ``None`` when absent or unreadable."""
    if not CONFORMANCE_JSON.is_file():
        return None
    try:
        return ConformanceReport.model_validate_json(CONFORMANCE_JSON.read_text())
    except ValueError:
        return None  # fail-closed for reuse: an unreadable report reuses nothing


def build_drafts(settings: Settings, *, force: bool = False) -> ConformanceReport:
    """Generate, gate, and persist the full draft grid; write the report.

    The grid is every in-scope part crossed with every document type (NPRM
    and final rule), so the drafting stage is parameterized, not a fixed list.
    Unchanged (part, doc_type) combinations are reused from the prior report;
    ``force`` regenerates everything.
    """
    export = AuthorityExport.model_validate_json(AUTHORITY_JSON.read_text())
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    previous = None if force else _previous_report()
    checklists: list[DraftChecklist] = []
    rejected_names: list[str] = []
    reused = 0
    for record in export.parts:
        part_text = _part_text(settings, record)
        corpus = _verification_corpus(settings, record)
        for doc_type in DOC_TYPES:
            dossier = _build_dossier(settings, record, doc_type, part_text)
            name = f"31-CFR-{record.part}-{doc_type}.txt"
            prior = _reusable_checklist(previous, dossier, record.part, doc_type)
            if prior is not None:
                checklists.append(prior)
                reused += 1
                if not prior.passed:
                    rejected_names.append(name)
                continue
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
        model_note=_model_note(checklists),
        rejected_drafts=rejected_names,
    )
    CONFORMANCE_JSON.write_text(report.model_dump_json(indent=2) + "\n")
    if reused:
        print(f"drafts: reused {reused} unchanged")
    return report


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    report = build_drafts(Settings(), force="--force" in args)
    print(
        f"drafts: {report.accepted}/{report.generated} accepted "
        f"(pass rate {report.pass_rate:.2f}), "
        f"{report.total_unverified_quotes} unverified quotes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
