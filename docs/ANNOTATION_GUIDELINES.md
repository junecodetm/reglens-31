# Gold-Set Annotation Guidelines (v1)

Unit of annotation: one **provision** = one sampled paragraph from `reglens/eval/gold/provisions.jsonl`. Labels are provision-level; the provision's own offsets are the span.

## Label: `is_obligation`

**TRUE** iff the provision's own text imposes a duty on an identifiable party to act or refrain from acting — operative language such as *must, shall, may not, is required to, is prohibited from, no person may*.

**FALSE** for:
- Definitions, scope/applicability statements, authority citations, effective-date notices.
- **Descriptions of obligations located elsewhere** — preamble/summary text like "the final rule requires banks to…" is a description, not operative text → FALSE. Amendatory text that quotes the operative regulation verbatim (e.g., "§ 1010.310 Each financial institution must…") → TRUE.
- Permissions and discretion ("may", "is authorized to") without a bound duty.

Obligations on a government actor ("The Secretary shall publish…") are TRUE with `affected_party` = that actor.

## If TRUE, also label

- `obligation_type`: one of `requirement | prohibition | reporting | recordkeeping | disclosure | other`. Reporting/recordkeeping/disclosure win over the generic `requirement` when applicable; `prohibition` for duties to refrain.
- `affected_party`: the bound party **as named in the text** (e.g., "each financial institution"), not a paraphrase.
- `effective_date`: only if stated **inside the provision**; else `null`.

## Tie-breaking

1. Mixed provisions (obligation + other content): TRUE if any operative duty is present; type = the dominant duty.
2. Conditional duties ("if X, the person must Y") are TRUE.
3. When genuinely uncertain after applying rules 1–2, label FALSE and say why in `rationale` (favors precision of the gold positives; flagged for adjudication either way).

## Record format (JSONL, one object per provision)

```json
{"provision_id": "…", "is_obligation": true, "obligation_type": "reporting",
 "affected_party": "each financial institution", "effective_date": null,
 "rationale": "operative 'must file' duty", "proposed_by": "<model>", "adjudicated": false}
```

`adjudicated` is ALWAYS `false` at proposal time. Machine proposals are not ground truth until a human adjudicates them (BUILD.md §4); metrics computed against un-adjudicated labels are labeled **Provisional**.
