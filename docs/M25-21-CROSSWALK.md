# OMB M-25-21 §4(b) Minimum-Practices Crosswalk

> EXTEND-OGC01 Stage 4. Practice names and the deadline text below were verified
> against the memo PDF itself (whitehouse.gov, M-25-21, issued 2025-04-03), not a
> secondary source. This is a demonstration mapping for an independent prototype;
> it is not a compliance claim, and this project is not a federal AI use case.

## Scope note

M-25-21 §4(a)(1) (verbatim): *"Within 365 days of the issuance of this memorandum,
agencies must document implementation of the minimum practices in Section 4(b) of
this memorandum for high-impact uses of AI and be prepared to report them to OMB,
as part of periodic accountability reviews, the annual AI use case inventory, or
upon request as determined by OMB. If a particular high-impact use case is not
compliant with the minimum practices then the agency must safely discontinue use
of the AI functionality."*

The 365-day clock (≈2026-04-03) and the discontinuation consequence apply to
high-impact uses of AI; §4(b)(ii) separately requires an AI impact assessment
*"before deploying"* a new high-impact use case — the memo's textual distinction
between in-operation and pre-deployment obligations. OGC-01 ("Regulatory Reform
Tool", Departmental Offices, high-impact) is listed as **Pre-Deployment**, so the
§4(b) practices are the gate it must clear before deployment. That is precisely
the stage this prototype demonstrates artifacts for.

## Crosswalk: §4(b) minimum practices → concrete artifacts in this repo

| # | M-25-21 §4(b) practice (memo's wording) | Artifact here that demonstrates it |
|---|---|---|
| i | Conduct Pre-Deployment Testing | `reglens/eval/` harness (P/R/F1 with 95% Wilson + clustered-bootstrap CIs over a versioned gold set); CI regression gate (`.github/workflows/eval.yml`, fails on F1 regression or citation fidelity < 1.0); week-one falsification tests (docs/BUILD_PLAN.md); Playwright end-to-end audit |
| ii | Complete AI Impact Assessment | `governance/ai_impact_assessment.md` (intended use, affected parties, failure modes, mitigations) |
| iii | Conduct Ongoing Monitoring for Performance and Potential Adverse Impacts | `governance/monitoring_plan.md` (staleness triggers, refresh/retirement policy, "data as of" banner); every push re-runs the eval gate on pinned fixtures |
| iv | Ensure Adequate Human Training and Assessment | `docs/ANNOTATION_GUIDELINES.md` (written labeling guidelines) + `docs/ADJUDICATE.md` (structured human-adjudication worklist; metrics restate from the JSONL as adjudication proceeds) |
| v | Provide Additional Human Oversight, Intervention, and Accountability (incl. fail-safe) | The fail-closed provenance gate (`reglens/provenance.py`): an unverifiable claim is dropped, never shown — the fail-safe that "minimizes the risk of significant harm"; rejected-claim counts are publicly visible; `governance/rollback_plan.md` (revert to last-good static export + pinned model) |
| vi | Offer Consistent Remedies or Appeals | Prototype scoping (honest): there are no end users whose determinations could require remedy — every displayed claim links to its primary source so any reader can check and refute it, and corrections land through the public issue tracker + adjudication worklist, restating metrics automatically |
| vii | Consult and Incorporate Feedback from End Users and the Public | Public repository with issues enabled; evaluation data, guidelines, and rejection counts published for inspection. Prototype scoping: no agency end-user population exists to consult |

## NIST AI 600-1 (Generative AI Profile) mapping

| AI 600-1 risk | Posture here |
|---|---|
| **Confabulation** | Structural, not advisory: every model claim must carry a verbatim source span that passes a deterministic exact-substring check (fail-closed); citation fidelity is reported as a guardrail metric and gated at 1.0 in CI; draft-skeleton narratives pass a fabrication scan (RIN/docket/dollar/date/contact patterns reject the draft) and an unverifiable-quote gate |
| **Information Integrity** | Content-addressed immutable snapshots (SHA-256) of every source with manifests (URL, fetch time, hash); deterministic replay (temperature 0, pinned model tag, prompt hash, input SHA recorded per run); SBOM + checksum-verified security tooling in CI; the deployed site is a pre-computed static artifact with no runtime network calls |

## Sources

- OMB M-25-21, "Accelerating Federal Use of AI through Innovation, Governance,
  and Public Trust" (2025-04-03), §§3, 4(a)(1), 4(b) — read from the memo PDF.
- NIST AI 600-1, Generative AI Profile (2024-07-26), Confabulation and
  Information Integrity risk categories.
- Treasury AI Use Case Inventory entry for OGC-01 (see docs/OGC01-ALIGNMENT.md).
