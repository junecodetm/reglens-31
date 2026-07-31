# AI Impact Assessment — RegLens-31 Prototype

## Purpose and benefit

RegLens-31 demonstrates auditable, provenance-gated extraction of regulatory
obligations. The capability corresponds to Treasury's "Document Processing and
Regulatory Intake" use-case family and high-impact use case OGC-01, whose
inventory component is General Counsel.

## Data handling

Obligation extraction runs locally and has no third-party egress. The committed
draft and review-memorandum narratives use the pinned Groq free-tier
`openai/gpt-oss-120b` model. Draft prompts send the part number, heading,
authority citation, and document type. Memorandum prompts also send derived
authority classifications and marker counts and bands. These inputs are public
regulatory metadata or deterministic evidence; they do not include corpus
documents.

The optional `/api/draft` endpoint sends the draft metadata and the
visitor-supplied policy objective to Groq. The objective is limited to 500
characters, neutralized as data rather than instructions, and leaves the
visitor's browser. The endpoint cannot determine whether a visitor has entered
sensitive content; visitors must not submit personal or non-public information.

## Rights and safety impact

The corpus pipeline ingests public regulatory text and no private-individual
PII. Source documents may contain official public contact information. The
system makes no decisions about individuals. Outputs support human review and
appear with a non-affiliation disclaimer.

## Failure modes and mitigations

The controls correspond to the NIST AI RMF MAP, MEASURE, and MANAGE functions.

- **Confabulated claims:** A fail-closed provenance gate rejects unverifiable
  quotations, and the interface reports rejection counts.
- **Missed obligations:** Recall is measured against a versioned evaluation set
  with confidence intervals. Metrics carry the label
  `Provisional — machine-proposed labels, human-adjudicated: N/M` until human
  adjudication is complete.
- **Prompt injection from source text or a policy objective:** Models execute
  no tools and fetch no URLs. Inputs are delimited, live policy objectives are
  neutralized as data, output is schema-constrained, and quotation checks
  provide an independent control.
- **Metric gaming or regression:** The CI evaluation gate uses committed
  fixtures and fails on an F1 regression or citation fidelity below 1.0.
- **Staleness:** The interface displays the source snapshot date.
  `governance/monitoring_plan.md` defines refresh and retirement criteria.
- **Hosted-service availability and quota:** Draft, memorandum, and live
  narrative generation depend on the shared Groq free tier. The live interface
  reports unavailability or quota exhaustion and falls back to a committed
  draft.
- **Live-gate coverage:** Committed drafts pass the full build-time conformance
  gate. Live output passes only the documented in-browser subset and is labeled
  accordingly.

## Human oversight

Every claim links to its primary source and highlights the exact supporting
span. The adjudication worklist in `docs/ADJUDICATE.md` restates metrics as
reviewers adjudicate labels.
