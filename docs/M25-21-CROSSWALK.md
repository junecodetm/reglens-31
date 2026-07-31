# OMB M-25-21 §4(b) Minimum-Practices Crosswalk

The practice names and deadline text are drawn from the M-25-21 memorandum
(WhiteHouse.gov, issued 2025-04-03). This crosswalk maps an independent
prototype's artifacts to the memorandum. It is not a compliance claim, and the
project is not a federal AI use case.

## Scope note

M-25-21 §4(a)(1) (verbatim): *"Within 365 days of the issuance of this memorandum,
agencies must document implementation of the minimum practices in Section 4(b) of
this memorandum for high-impact uses of AI and be prepared to report them to OMB,
as part of periodic accountability reviews, the annual AI use case inventory, or
upon request as determined by OMB. If a particular high-impact use case is not
compliant with the minimum practices then the agency must safely discontinue use
of the AI functionality."*

The 365-day deadline (approximately 2026-04-03) and the discontinuation
requirement apply to high-impact uses of AI. Section 4(b)(ii) separately
requires an AI impact assessment *"before deploying"* a new high-impact use
case, distinguishing operational obligations from pre-deployment obligations.
OGC-01 ("Regulatory Reform Tool," Departmental Offices, high-impact) is listed
as **Pre-Deployment**. This prototype demonstrates artifacts relevant to that
pre-deployment gate without asserting that the artifacts satisfy it.

## Section 4(b) minimum-practices crosswalk

| # | M-25-21 §4(b) practice (memo's wording) | Artifact mapping |
|---|---|---|
| i | Conduct Pre-Deployment Testing | `reglens/eval/` harness (P/R/F1 with 95% Wilson and clustered-bootstrap CIs over a versioned gold set); CI regression gate (`.github/workflows/eval.yml`, which fails on F1 regression or citation fidelity below 1.0); Playwright end-to-end audit; full local verification through `just ci`, documented in `docs/COMMANDS.md` |
| ii | Complete AI Impact Assessment | `governance/ai_impact_assessment.md` (intended use, affected parties, failure modes, mitigations) |
| iii | Conduct Ongoing Monitoring for Performance and Potential Adverse Impacts | `governance/monitoring_plan.md` defines snapshot-age triggers and refresh or retirement controls. Every push runs the evaluation gate against pinned fixtures. |
| iv | Ensure Adequate Human Training and Assessment | `docs/ANNOTATION_GUIDELINES.md` defines labeling criteria, and `docs/ADJUDICATE.md` defines the human-adjudication procedure. The prototype has no agency workforce or training program. |
| v | Provide Additional Human Oversight, Intervention, and Accountability (incl. fail-safe) | The fail-closed provenance gate in `reglens/provenance.py` rejects unverifiable claims and reports rejection counts. `governance/rollback_plan.md` defines recovery to a known-good static export and pinned model. |
| vi | Offer Consistent Remedies or Appeals | No remedies or appeals process is implemented because the prototype makes no determinations about people. Each displayed claim links to its primary source, and the public issue tracker and adjudication worklist support corrections. |
| vii | Consult and Incorporate Feedback from End Users and the Public | The public repository exposes issues, evaluation data, guidelines, and rejection counts for review. No agency end-user population exists for consultation. |

## NIST AI 600-1 (Generative AI Profile) mapping

| AI 600-1 risk | Posture here |
|---|---|
| **Confabulation** | Structural, not advisory: every extracted claim must carry a verbatim source span that passes a deterministic exact-substring check (fail-closed); citation fidelity is reported as a guardrail metric and gated at 1.0 in CI; committed draft narratives pass the complete fabrication and unverifiable-quote gates; optional live narratives pass the disclosed in-browser gate subset and fall back to committed drafts on failure |
| **Information Integrity** | Content-addressed immutable snapshots (SHA-256) of every source with manifests (URL, fetch time, hash); deterministic replay (temperature 0, pinned model tag, prompt hash, input SHA recorded per run); SBOM and checksum-verified security tooling in CI; a precomputed core site and read API that require no runtime network call; an optional same-origin live drafting endpoint with committed-draft fallback |

## Sources

- OMB M-25-21, "Accelerating Federal Use of AI through Innovation, Governance,
  and Public Trust" (2025-04-03), §§3, 4(a)(1), and 4(b).
- NIST AI 600-1, Generative AI Profile (2024-07-26), Confabulation and
  Information Integrity risk categories.
- Treasury AI Use Case Inventory entry for OGC-01 (see
  `docs/OGC01-ALIGNMENT.md`).
