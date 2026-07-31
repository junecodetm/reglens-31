# Governance mapping (NIST, OMB, and OSCAL)

The repository's governance artifacts are the model card, data card, AI impact
assessment, monitoring plan, and rollback plan under `governance/`. OSCAL
component-definition and validation work is outside the implemented scope, as
recorded in [docs/CHECKLIST.md](CHECKLIST.md).

## Policy baseline

The baseline comprises OMB M-25-21, "Accelerating Federal Use of AI through
Innovation, Governance, and Public Trust" (issued 2025-04-03 and replacing
M-24-10); OMB M-25-22 on AI acquisition and E.O. 14179 implementation; the
2025-07-23 "Winning the Race: America's AI Action Plan"; NIST AI RMF 1.0
(AI 100-1) GOVERN, MAP, MEASURE, and MANAGE; NIST Generative AI Profile
AI 600-1 (2024-07-26), including prompt injection (§2.9) and confabulation;
NIST SSDF SP 800-218 and 800-218A; SP 800-204D; FISMA and SP 800-53; FedRAMP
RFC-0024 (published 2026-01-13, with OSCAL deadlines of 2026-09-30 and
2027-09-30); Zero Trust memorandum M-22-09; Section 508; WCAG 2.1 AA; the
21st Century IDEA Act; and USWDS.

## Treasury alignment

Treasury's September 2025 AI Strategy for M-25-21 identifies "Document
Processing and Regulatory Intake" and "Financial Detection and Risk Analysis"
as priority use-case families. It describes an AI Governance Board, AI
Transformation Office, AI Council, and FISMA-High AI Sandbox. The companion
Compliance Plan places generative AI in a certified FISMA-moderate pilot
environment.

FedScoop reports that Treasury's published inventory increased from 54 use
cases in 2024 to 129, including 61 IRS use cases and 26 Office of the
Comptroller of the Currency use cases. Four of the 129 rows are marked
`High-impact`; OGC-01, "Regulatory Reform Tool," is the only high-impact row
outside the IRS. References to OGC-01 as a Departmental Offices use case are an
organizational gloss: the CSV records its `Bureau/Component` value as
`General Counsel`, and it is the inventory's only General Counsel row.

The inventory contains no FinCEN use case and no operational sanctions-screening
AI use case. It identifies an aspirational, unfunded OFAC public chatbot
(TFI-1). RegLens-31 maps to OGC-01 and the regulatory-intake family but does not
claim to be a sanctions-screening system. Its use and presentation remain
subject to the [Framing constraints](OGC01-ALIGNMENT.md#framing-constraints--non-negotiable).

## NIST AI RMF crosswalk

- GOVERN: invariants, model and data cards, and rollback plan.
- MAP: intended use, non-goals, and AI impact assessment.
- MEASURE: the custom eval harness (`reglens/eval/`), Wilson intervals,
  clustered-bootstrap intervals, and citation fidelity.
- MANAGE: CI regression gate, monitoring plan, and human review.

The M-25-21 minimum practices for impact assessment, ongoing monitoring, human
oversight, documentation, and public transparency map to the artifacts under
`governance/`.

## DHS/ALL/PIA-097 reference alignment

The OGC-01 inventory row cites DHS/ALL/PIA-097, "Use of Conditionally Approved
Commercial Generative AI Tools," as its associated PIA. PIA-097 is a retired DHS
artifact and does not bind this project. It serves only as a reference baseline
for commercial-generative-AI privacy controls:

- Public-source corpus; no PII, classified information, or internal data:
  enforced through the NO-RESTRICTED-DATA invariant and the source allow-list in
  `docs/DATA_SOURCES.md`.
- Vendor training, retention, and approved-tool controls: regulatory extraction
  is local-only and has no third-party egress. Optional draft and memorandum
  narratives send only public regulatory metadata to the configured Groq
  provider; the live drafting endpoint may also send the visitor's own policy
  objective. These paths never send corpus documents or restricted data and
  retain the provider risks documented in `docs/SECURITY.md`.
- Human review before use: outputs are assistive, never the sole basis for
  action, and carry the UI, README, and model-card disclaimers.
- Accuracy and factuality: the fail-closed provenance gate and custom evaluation
  harness report confidence intervals and reject unverifiable quoted spans.
- Bias and DEIA review: outputs are grounded in regulatory text and contain no
  individual-level data. Incidental statutory references to protected-class
  benefit programs, including disability and veterans' payments in 31 CFR 285,
  pass through verbatim. `governance/ai_impact_assessment.md` records the
  residual risk.
- Logging and auditability: run manifests record the model identifier, prompt
  hash, and input SHA; structured logs apply PII redaction.

Local extraction eliminates the commercial-vendor relationship for the
evidentiary pipeline. Optional provider-backed narrative generation retains a
vendor relationship and therefore requires the corresponding approved-tool,
retention, and training controls.

## OSCAL scope

The repository does not include `governance/component-definition.json` or
OSCAL validation in CI. This de-scope means the prototype does not demonstrate
FedRAMP RFC-0024 OSCAL readiness. The final scope decision is recorded in
[docs/CHECKLIST.md](CHECKLIST.md).

The implemented governance artifacts are:

- `governance/model_card.md`;
- `governance/data_card.md`;
- `governance/ai_impact_assessment.md`;
- `governance/monitoring_plan.md`, including drift and staleness triggers; and
- `governance/rollback_plan.md`, including reversion to the last known-good
  static export and pinned model.
