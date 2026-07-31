# Submission checklist & scope decisions

A checked item has repository or deployed evidence. Unchecked items require the final rebuild, CI run, accessibility audit, or live-service verification.

## Verified controls

- [x] The public repository contains setup, operating, architecture, security, evaluation, governance, and licensing documentation.
- [x] The deployed static site is available at https://reglens-31.pages.dev and the committed export operates without an API key.
- [x] `just demo` serves the pre-computed site fully offline after setup.
- [x] The deterministic provenance gate rejects fabricated or unverifiable quotations; accepted and rejected records remain visible for review.
- [x] The static read API publishes typed artifacts under `/api/v1/` with a generated OpenAPI 3.1 document and contract tests.
- [x] Evaluation reports precision, recall, and F1 with Wilson and document-clustered bootstrap intervals, ICC/design effect, citation fidelity, and Cohen's kappa. Results are labeled **Provisional — machine-proposed labels, human-adjudicated: 0/251**. Kappa is CROSS-MODEL agreement between two different frontier models, never human inter-annotator agreement.
- [x] Model and data cards, an AI impact assessment, a monitoring plan, and a rollback plan are present under `governance/`.
- [x] CI greps the pinned non-affiliation wording in the README and every built page. The full README disclaimer retains the 31 U.S.C. §333 text.
- [x] `DATA_LICENSE.md` records data provenance. OpenSanctions is not used; its CC-BY-NC 4.0 restriction and attribution requirement are retained for the de-scoped ownership design.
- [x] The zero-cost checker enforces pinned actions and dependency, service, and host allow-lists.

## Pending final verification

- [x] Complete the local extraction sample and run the final rebuild so published corpus counts and derived artifacts are regenerated from one claims file. All 25 sampled documents are extracted under a single recorded runtime; a bare re-run reuses every document and leaves `claims.json` byte-identical.
- [x] Confirm that the published draft grid contains all 10 combinations: five parts × NPRM/final, each accepted by the full conformance gate. The rebuild reports 10/10 accepted with zero unverified quotes.
- [ ] Verify the deployed `/api/draft` path with the pinned Groq free tier, including successful generation, the subset-check label, quota handling, and fallback to a committed fully gated draft.
- [x] Confirm that review memoranda for all five in-scope parts are exported and displayed with deterministic evidence, equal treatment of both marker families, and a gated model-generated narrative or explicit narrative rejection. The rebuild reports 5/5 narratives accepted; display is covered by the browser contract tests.
- [x] Confirm that the obligations dashboard filters by acceptance status, obligation type, affected party, and free text before preview limits are applied, and that neutral review signals remain available. Covered by the routes-contract browser tests against the built export.
- [x] Re-run evaluation and confirm the live adjudication counts, intervals, citation fidelity, and cross-model kappa in the exported site and static API. Citation fidelity is 1.000 and the provisional labels carry the current adjudication counts.
- [x] Run the complete CI, browser contract, and WCAG 2.1 AA accessibility checks against the rebuilt static export. All local gates pass: lint, strict types, 294 Python tests, 81 browser contract tests, and pa11y WCAG 2.1 AA on all six routes.
- [ ] Deploy the rebuilt export and complete a cold-load smoke test of every route, the static API, source-span interaction, rejection evidence, filters, memoranda, and drafting fallback.

## Scope decisions

### De-scoped

- **OFAC 50% ownership graph.** The implementation is excluded; the entity-resolution design, coverage limitations, and OpenSanctions CC-BY-NC caveat remain in `docs/ENTITY_RESOLUTION.md`.
- **OSCAL component-definition validation.** The governance artifacts are maintained as Markdown; no OSCAL 1.1.3 component definition or validation step is included.
- **SLSA Level 3, cosign, and OpenSSF Scorecard.** Existing CI security scans and SBOM generation remain; provenance level, attestation signing, and Scorecard integration are excluded.
- **Commit signing.** Contributions use pull requests, Conventional Commits, squash merge, and CI gates; signed commits are not required.
- **Inspect AI wrapper.** Evaluation uses the custom harness in `reglens/eval/` because the project must own its Wilson and rule-clustered bootstrap statistics. `inspect-ai` is not a dependency.
- **Hosted-model escalation for extraction.** Obligation extraction is local-only. The pinned Groq free tier is limited to the generative draft, memorandum, and optional live-drafting stages.

### Categorically excluded

- CourtListener as a runtime or ingestion dependency.
- QuantGov or RegData ingestion; those projects may be cited only as prior art.
- Judicial-outcome prediction or any claim about a rule's legal validity.
- Ranked repeal, vulnerability, or change-candidate lists.
- Expansion into additional 31 CFR Chapter V or Chapter X material. Part 501 remains the sole in-scope Chapter V part and is limited to procedural reporting, recordkeeping, licensing, and penalty provisions.
