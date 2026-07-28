# AI Impact Assessment — RegLens-31 (prototype-scoped)

**Purpose & benefit:** demonstrate auditable, provenance-gated extraction of regulatory obligations (maps to Treasury's "Document Processing and Regulatory Intake" use-case family and DO high-impact use case OGC-01) with zero data egress.

**Rights/safety impact:** minimal by construction — public regulatory text only; no PII ingested; no decisions about individuals; outputs are assistive with a human in the loop and a visible non-affiliation disclaimer.

**Failure modes & mitigations (NIST AI RMF MAP/MEASURE/MANAGE):**
- *Confabulated claims* → fail-closed provenance gate rejects unverifiable quotes; rejection counts are public in the UI.
- *Missed obligations (recall)* → measured against a versioned gold set with honest CIs; provisional labeling until adjudication.
- *Prompt injection from source text* → no tools, no fetching, delimited data, schema-constrained output, gate as backstop.
- *Metric gaming/regression* → CI eval gate on committed fixtures fails the build on F1 regression or fidelity < 1.0.
- *Staleness* → dated snapshot with "as of" footer; refresh policy in monitoring_plan.md.

**Human oversight:** every claim links to its primary source with the exact span highlighted; adjudication worklist (`docs/ADJUDICATE.md`) restates metrics as humans rule on labels.
