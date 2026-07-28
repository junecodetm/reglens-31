# Pre-Submission Checklist

> Decomposed from CLAUDE.md §22 (2026-07-28).

- [ ] Public GitHub repo with README (setup/run, approach, tools, assumptions) — deliverable #1.
- [ ] Live static reviewer URL on Cloudflare Pages loads cold, offline-safe, <10s to value — deliverable #2.
- [ ] `just demo` runs with no API key, fully offline.
- [ ] Provenance gate demonstrably rejects a fabricated quote (test + visible counter).
- [ ] Eval page shows P/R/F1 with Wilson + clustered-bootstrap CIs and Cohen's kappa.
- [ ] OFAC ownership graph renders the seeded Deripaska (70%→44.95%) case with caveats.
- [ ] Governance: OSCAL 1.1.3 validates; model/data cards, AI impact assessment, monitoring + rollback plans present.
- [ ] Security: SBOM, cosign attestation, CodeQL/Semgrep/gitleaks/pip-audit/osv-scanner green; Scorecard run.
- [ ] Accessibility: pa11y-ci + axe + Lighthouse pass (Section 508 / WCAG 2.1 AA); screen-reader matrix noted.
- [ ] Non-affiliation disclaimer in README, site footer, and repo description (31 U.S.C. §333).
- [ ] OpenSanctions CC-BY-NC attribution present in DATA_LICENSE.md and on the site.
- [ ] Zero-cost check passes; no card anywhere; `scripts/check_zero_cost.py` green.
- [ ] Staleness note on the deployed demo (dated snapshot; "as of" banner; monitoring_plan describes refresh/retirement).
