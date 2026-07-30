# Pre-Submission Checklist

> Decomposed from CLAUDE.md §22 (2026-07-28). Status as of the 2026-07-28 single-pass build (docs/PROGRESS.md).

- [x] Public GitHub repo with README (setup/run, approach, tools, assumptions) — deliverable #1.
- [x] Live static reviewer URL on Cloudflare Pages loads cold, offline-safe, <10s to value — deliverable #2 (https://reglens-31.pages.dev).
- [x] `just demo` runs with no API key, fully offline (verified on a fresh clone).
- [x] Provenance gate demonstrably rejects a fabricated quote (unit + hypothesis tests; 163 real rejections visible in the UI counter and transparency section).
- [x] Eval page shows P/R/F1 with Wilson + clustered-bootstrap CIs and Cohen's kappa — labeled **Provisional** (machine-proposed labels, 0/251 human-adjudicated; kappa is cross-model agreement, human κ pending adjudication).
- [ ] OFAC ownership graph renders the seeded Deripaska (70%→44.95%) case with caveats — **de-scoped** (first item in the sanctioned de-scope order; design retained in docs/ENTITY_RESOLUTION.md).
- [ ] Governance: OSCAL 1.1.3 validates — **de-scoped**; model/data cards, AI impact assessment, monitoring + rollback plans ARE present in `governance/`.
- [x] Security: SBOM artifact, CodeQL/Semgrep/gitleaks/pip-audit/osv-scanner green in CI (checksum-verified binaries). Cosign attestation + Scorecard: deferred with SLSA (de-scope order item 3).
- [x] Accessibility: axe-core zero violations with full keyboard operability verified via the Playwright audit at 1440/768/375 (re-verified in the 2026-07-29 final pass, including skip-link-first tab order from a cold load); `just a11y` runs pa11y WCAG2AA.
- [x] Non-affiliation disclaimer in README, site header band + footer, and repo description (31 U.S.C. §333).
- [x] Data licensing: DATA_LICENSE.md provenance table (OpenSanctions not used in this build; CC-BY-NC term documented for the future ownership module).
- [x] Zero-cost check passes; no card anywhere; `scripts/check_zero_cost.py` green (real allow-list check: pinned actions, dependency + host allow-lists).
- [x] Staleness note on the deployed demo ("data as of" footer; refresh/retirement policy in governance/monitoring_plan.md).
