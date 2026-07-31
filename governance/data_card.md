# Data Card — RegLens-31 Snapshots and Evaluation Set

## Sources

- Federal Register API v1: Treasury final rules amending the in-scope parts
  (public domain).
- eCFR versioner API: Title 31 parts 50, 223, 285, 356, and 501 at a pinned
  point-in-time date (U.S. Government work; unofficial compilation), including
  the per-part section census and amendment dates used for the currency
  comparison.

All fetches pass the runtime allow-list in `reglens/ingest/allowlist.py`. The
same module enforces exclusions for BSA/SAR data, FinCEN BOI data, taxpayer
data, private PII, and authenticated or paywalled content. CI scans for these
categories.

## Ingested corpus vs extracted sample

`reglens/corpus.py` enforces separate ingestion and extraction boundaries:

- **Ingested (157 documents).** The corpus contains 152 Federal Register documents and five eCFR part texts. The Federal Register documents comprise every final rule the FR CFR index attributes to an in-scope part (132) and 20 citation-following documents. All source documents are committed as content-addressed snapshots.
- **Extraction sample (25 documents).** `in_extraction_sample` selects the five part texts and every in-scope Federal Register document published in `EXTRACTION_YEAR` (2026). Local laptop inference limits routine extraction to this deterministic sample; `python -m reglens.extract --all` processes the full corpus. `tests/test_corpus.py` requires the persisted claim set to equal the rule's selection, and [docs/CHECKLIST.md](../docs/CHECKLIST.md) retains final verification of that contract.

The sample contract reads the five part texts in full and caps Federal Register documents at 80,000 characters. Each completed record carries `total_chars` and `extracted_chars`. The exporter computes `documents_extracted` against `documents_in_scope` in `reglens/store/corpus_scope.py` for both the site and `/api/v1/index.json`.

The 251 evaluation provisions are drawn from the extracted sample. Reported
metrics therefore characterize that sample, not the full ingested corpus.

## Provenance and versioning

Raw snapshots are immutable and content-addressed under `data/raw/<sha256>/`.
Each manifest records the source identifier, URL, fetch time, and hash. Derived
extraction claims are reproducible from the snapshots, pinned local model,
temperature 0, and fixed seed. Evaluation proposals are versioned separately;
each record identifies its source SHA and proposing model, and adjudication
changes only the versioned gold records.

## Evaluation set

The 251 provisions are sampled deterministically with a fixed seed in two
disclosed strata, recorded as `stratum` on each record:

1. `base`: seven paragraphs per document across all 25 documents.
2. `ecfr-supplement`: additional obligation-dense paragraphs from the operative
   eCFR parts.

Pooled precision combines strata with different selection rates. `eval.json`
therefore reports per-stratum metrics.

Labels follow `docs/ANNOTATION_GUIDELINES.md`. Two frozen, independent labeling
runs use two different frontier models: `claude-fable-5` and
`claude-sonnet-5`. Each record identifies its model in `proposed_by`, and
`pass1.jsonl` and `pass2.jsonl` preserve the original proposals separately from
adjudication. The reported Cohen's kappa on `is_obligation` is CROSS-MODEL
agreement between two different frontier models; it is not human
inter-annotator agreement. Same-model repeat agreement is excluded because it
measures repeatability rather than independent agreement.

Machine-proposed labels are not ground truth. Records carry
`adjudicated: false` until a human adjudicates them. Published metrics carry
`Provisional — machine-proposed labels, human-adjudicated: N/M`, with the
applicable counts substituted for `N/M`, until adjudication is complete.
