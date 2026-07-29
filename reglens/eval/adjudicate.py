"""Generate docs/ADJUDICATE.md — the human adjudication worklist.

Inputs: the merged gold set and its provisions. Outputs: a numbered Markdown
worklist in ~20-item evening batches. Failure mode: missing gold files raise;
the worklist is regenerated, never hand-edited (progress lives in gold.jsonl).
"""

from pathlib import Path

from reglens.eval.gold_records import load_jsonl, load_provisions
from reglens.eval.harness import GOLD_DIR

BATCH_SIZE = 20


def render_worklist(gold_dir: Path = GOLD_DIR) -> str:
    provisions = load_provisions(gold_dir / "provisions.jsonl")
    gold = load_jsonl(gold_dir / "gold.jsonl")
    adjudicated = sum(1 for record in gold if record.adjudicated)

    lines = [
        "# Adjudication Worklist",
        "",
        f"Progress: **{adjudicated}/{len(gold)} adjudicated.** Labels below are",
        "machine-proposed (see `proposed_by`) and are NOT ground truth until you rule on them.",
        "",
        "## How to adjudicate an item",
        "",
        "1. Read the provision text against `docs/ANNOTATION_GUIDELINES.md`.",
        "2. In `reglens/eval/gold/gold.jsonl`, find the line with the item's `provision_id`.",
        '3. **Accept:** set `"adjudicated": true`. **Edit:** correct the label fields,',
        '   then set `"adjudicated": true`. **Reject the provision entirely:** delete the line',
        "   (and note why in your commit message).",
        "4. Commit; the eval label and this file's counts update from the JSONL",
        "   (`just eval` regenerates metrics; `uv run python -m reglens.eval.adjudicate`",
        "   regenerates this worklist).",
        "",
    ]
    for index, record in enumerate(gold):
        if index % BATCH_SIZE == 0:
            evening = index // BATCH_SIZE + 1
            lines.append(
                f"## Evening {evening} (items {index + 1}-{min(index + BATCH_SIZE, len(gold))})"
            )
            lines.append("")
        provision = provisions[record.provision_id]
        status = "✅ adjudicated" if record.adjudicated else "⬜ pending"
        text = " ".join(provision.text.split())
        if len(text) > 400:
            text = text[:400] + "…"
        lines.extend(
            [
                f"### {index + 1}. `{record.provision_id}` — {status}",
                "",
                f"- **Document:** {provision.document_number}"
                f" (chars {provision.start}-{provision.end})",
                f"- **Provision:** {text}",
                f"- **Proposed:** is_obligation={record.is_obligation}"
                + (f", type={record.obligation_type}" if record.obligation_type else "")
                + (f", party={record.affected_party}" if record.affected_party else "")
                + (f", effective={record.effective_date}" if record.effective_date else ""),
                f"- **Rationale ({record.proposed_by}):** {record.rationale}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_ogc01_worklist() -> str:
    """EXTEND-OGC01 gold sets, appended in the same numbered-worklist format."""
    from reglens.eval.ogc01 import (
        GOLD_AUTHORITY,
        GOLD_GROUNDING,
        ClassRecord,
        LinkRecord,
        MarkerJudgment,
        load_typed_jsonl,
    )

    class_gold = load_typed_jsonl(GOLD_AUTHORITY / "class_gold.jsonl", ClassRecord)
    links_gold = load_typed_jsonl(GOLD_AUTHORITY / "links_gold.jsonl", LinkRecord)
    grounding_gold = load_typed_jsonl(GOLD_GROUNDING / "gold.jsonl", MarkerJudgment)
    total = len(class_gold) + len(links_gold) + len(grounding_gold)
    adjudicated = sum(
        1
        for record in [*class_gold, *links_gold, *grounding_gold]
        if getattr(record, "adjudicated", False)
    )
    lines = [
        "",
        "# EXTEND-OGC01 Adjudication Worklist",
        "",
        f"Progress: **{adjudicated}/{total} adjudicated.** Same protocol as above:",
        'find the record in its JSONL file, correct if needed, set `"adjudicated": true`,',
        "commit; `just eval` restates the metrics and their label automatically.",
        "",
        f"## A. Classifications ({len(class_gold)} items) — "
        "`reglens/eval/gold/authority/class_gold.jsonl`",
        "",
        "Check each against the U.S.C. section text (`web/public/data/usc/"
        "usc-<title>-s<section>.txt`) and docs/ANNOTATION_GUIDELINES.md §OGC-01.",
        "",
    ]
    for index, record in enumerate(class_gold):
        if index % BATCH_SIZE == 0:
            lines.append(f"### Batch A{index // BATCH_SIZE + 1}")
            lines.append("")
        assert isinstance(record, ClassRecord)
        status = "✅" if record.adjudicated else "⬜"
        lines.append(
            f"{index + 1}. {status} `{record.pair_id}` — proposed "
            f"**{record.classification}** ({record.proposed_by}); {record.rationale}"
        )
    lines += [
        "",
        f"## B. Citation pairs ({len(links_gold)} items) — "
        "`reglens/eval/gold/authority/links_gold.jsonl`",
        "",
        "Check each (part → title, section) pair against the verbatim authority line",
        "shown in the Statutory authority UI section (or the eCFR).",
        "",
        f"## C. Grounding markers ({len(grounding_gold)} items) — "
        "`reglens/eval/gold/grounding/gold.jsonl`",
        "",
        "For `judgment` records: confirm the genuine/not-genuine call in document",
        "context. For `missed` records: confirm the occurrence exists and name its family.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    out_path = Path("docs/ADJUDICATE.md")
    out_path.write_text(render_worklist() + render_ogc01_worklist())
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
