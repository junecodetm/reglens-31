# Model Card — RegLens-31 Extraction Pipeline

## System and model

The system extracts obligations from U.S. federal regulatory text and applies a
deterministic, fail-closed provenance check. It runs `qwen3:8b` through Ollama
on local Apple Silicon with temperature 0, a fixed seed, and
JSON-schema-constrained output. It uses no fine-tuning. Every run records the
model tag, prompt SHA-256, and input SHA-256.

## Intended use

The system supports human triage of regulatory obligations. Every output links
to its primary source and is verified against that source. The output is not
legal advice, a compliance determination, or sanctions screening.

## Out-of-scope uses

Any autonomous compliance decision; any use on non-public or restricted data (BSA/SAR, FinCEN BOI, taxpayer data, private PII — prohibited by the ingest allow-list); any representation as a government system (31 U.S.C. §333).

## Factors and limitations

- Local models with approximately 8 billion parameters have limited
  whole-document extraction accuracy. The provenance gate enforces verbatim
  quotation fidelity but cannot recover missed obligations; recall is measured,
  not guaranteed.
- Long documents are extracted up to a disclosed per-document character cap,
  recorded as `total_chars` and `extracted_chars`.
- The supported corpus is limited to English-language U.S. federal regulatory
  register and eCFR text.

## Metrics

The evaluation view and `web/public/data/eval.json` report provision-level
precision, recall, and F1 with 95% Wilson and clustered-bootstrap intervals,
ICC/design effect, citation fidelity, and Cohen's kappa. The reported kappa is
CROSS-MODEL agreement between two different frontier models; it is not human
inter-annotator agreement. Metrics carry
`Provisional — machine-proposed labels, human-adjudicated: N/M`, with counts
derived from the versioned evaluation set, until adjudication is complete.

## Safety and security posture

The model executes no tools, has no network access, receives documents as
delimited data, and produces schema-constrained output. The fail-closed gate
rejects any claim whose quotation is not verbatim in the source. See
`docs/SECURITY.md` and NIST AI 600-1 §2.9 on confabulation and prompt injection.
