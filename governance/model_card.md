# Model Card — RegLens-31 Extraction Pipeline

**System:** obligation extraction over U.S. federal regulatory text, gated by a deterministic fail-closed provenance check.
**Model:** `qwen3:8b` via Ollama (local, Apple Silicon), temperature 0, fixed seed, JSON-schema-constrained output. No fine-tuning. Every run records model tag, prompt SHA-256, and input SHA-256.

## Intended use
Assistive triage of regulatory obligations for human review. Every output links to and is verified against its primary source. **Not** legal advice, **not** a compliance determination, **not** a sanctions-screening system.

## Out-of-scope uses
Any autonomous compliance decision; any use on non-public or restricted data (BSA/SAR, FinCEN BOI, taxpayer data, private PII — prohibited by the ingest allow-list); any representation as a government system (31 U.S.C. §333).

## Factors & limitations
- Whole-document extraction accuracy for local ~8B models is a known hard problem; the provenance gate enforces a precision floor on quotes (fidelity 1.0 by construction) but cannot recover missed obligations (recall is measured, not guaranteed).
- Long documents are extracted up to a disclosed per-document character cap (recorded per document as `total_chars` / `extracted_chars`).
- English-only; U.S. federal regulatory register/eCFR text only.

## Metrics
See the live eval section and `web/public/data/eval.json`: provision-level P/R/F1 with 95% Wilson and clustered-bootstrap intervals, ICC/design effect, citation fidelity, Cohen's kappa. Metrics are **Provisional — machine-proposed gold labels** until human adjudication completes (`docs/ADJUDICATE.md`); the label updates automatically from the versioned gold set.

## Safety & security posture
Prompt injection is mitigated structurally: the model executes no tools, fetches nothing, sees documents only as delimited data, and its output is schema-constrained; the fail-closed gate drops any claim whose quote is not verbatim in the source (docs/SECURITY.md; NIST AI 600-1 §2.9 confabulation/injection).
