# Phased Build Plan + Week-One Falsification Tests

> Decomposed from CLAUDE.md §14, §15, and the [VERIFY] appendix (2026-07-28).

## Phased build plan

Total 120–160 focused hours, 10–12 weeks part-time, solo. End-to-end vertical slice by week 5.

- **Phase 0 (wk 1, ~12h):** repo scaffold, uv/ruff/pyright, devcontainer, justfile, CI skeleton, local model pulled and JSON-schema output verified, zero-cost check. **Exit:** `just demo` runs a trivial end-to-end on one seeded doc, fully offline. **De-scope switch:** if react-uswds+React 19 fails, drop to plain USWDS HTML/CSS. *(TODO from decomposition: `scripts/check_zero_cost.py` is currently a stub that exits 0 — the real allow-list check against docs/STACK.md is Phase 0 work. The `.github/workflows/` CI skeleton is also not yet written.)*
- **Phase 1 (wk 2–3, ~30h):** ingest (Federal Register + eCFR T31 + OFAC + GLEIF snapshots, content-addressed); extract with provenance gate; SQLite/DuckDB/Parquet store. **Exit:** obligations extracted + verified on ≥20 real provisions; rejected-claim counter works.
- **Phase 2 (wk 4–5, ~30h):** Next.js static export UI — obligation list, click-to-highlight source span, rejected-claim banner; deploy to Cloudflare Pages. **Exit:** a cold reviewer opens the URL and sees value in <10s; Lighthouse/pa11y a11y pass.
- **Phase 3 (wk 6–7, ~30h):** evaluation — gold set ≥200, annotation + kappa, Inspect harness, Wilson + clustered bootstrap, CI regression gate on fixtures. **Exit:** metrics page renders with honest CIs.
- **Phase 4 (wk 8–9, ~25h):** OFAC 50% ownership module seeded with the Deripaska case + optional live matching with caveats; governance artifacts + OSCAL validation. **Exit:** ownership graph renders the seeded case; `just govern` passes.
- **Phase 5 (wk 10–12, ~25h):** DevSecOps hardening (SBOM, cosign, Scorecard, CodeQL), docs, README zero-friction path, non-affiliation disclaimer, pre-submission checklist. **Exit:** all CI green; checklist complete.

**Explicit de-scope switches (pull in this order if time runs short):** (1) drop live OFAC matching, keep the seeded case; (2) drop the optional Fiscal Data secondary demo; (3) drop SLSA L3; (4) reduce the gold set to 150 (Wilson CI still reported); (5) drop Groq escalation, ship local-only.

**Signal-to-effort ranking of "expected extras" (do the top ones, skip the bottom):** DO — data lineage via content-addressed snapshots, idempotency/replay, secrets handling + PII redaction, code license (Apache-2.0) + data attribution, staleness "as of" banner, browser/screen-reader test matrix (Chrome+VoiceOver, Firefox+NVDA-notes). SKIP for a solo prototype — full backup/DR for the demo (a static export is trivially redeployable), heavyweight release automation beyond semver tags, and a formal CONTRIBUTING beyond a short file.

## Week-one falsification tests (high-risk assumptions)

No downstream work may depend on an unverified assumption. Each risky assumption gets a cheap week-one test and a pre-decided pivot.

- **W1-1 Local model quality for constrained legal extraction.** *Test:* run the chosen local model with JSON-schema constraint on 15 hand-picked Title 31 provisions; measure exact-span citation rate and obligation precision. *Falsifies if:* precision <0.75 or span exactness <0.9. *Pivot:* escalate hard cases to the Groq free tier; if still weak, switch to a specialized extractor (NuExtract-class) or narrow scope to a cleaner obligation subtype.
- **W1-2 react-uswds 11.x + React 19 + Next.js static export.** *Test:* scaffold and static-export a one-page USWDS site. *Falsifies if:* build breaks or components error. *Pivot:* React 18, or plain USWDS 3 HTML/CSS.
- **W1-3 OFAC→GLEIF live match yield.** *Test:* reproduce ≥1 clean real ownership link beyond the seeded case via OpenSanctions. *Falsifies if:* zero clean, demonstrable links. *Pivot:* ship seeded-only, label live matching "experimental, human-review-required."
- **W1-4 OFAC SLS fetch.** *Test:* fetch SDN_ADVANCED.XML with a User-Agent header. *Falsifies if:* 403/schema drift. *Pivot:* use OpenSanctions' OFAC mirror.
- **W1-5 Zero-cost hosting end-to-end.** *Test:* deploy a static build to Cloudflare Pages with no card. *Falsifies if:* a card is demanded. *Pivot:* GitHub Pages.
- **W1-6 CI eval at $0.** *Test:* run Inspect over fixtures in GitHub Actions with no API key. *Falsifies if:* it needs a paid model. *Pivot:* local-model fixtures only (already the plan).

## Appendix — items explicitly marked [VERIFY AT BUILD TIME]

1. Exact local model + quantization that clears W1-1 on real Title 31 text.
2. `@trussworks/react-uswds` 11.x compatibility with React 19 + Next.js 15 static export (W1-2).
3. ~~Whether the pinned Inspect AI release exposes native confidence-interval metrics (else compute in-repo).~~ **Resolved:** Inspect AI was not adopted; Wilson + clustered bootstrap + kappa are computed in `reglens/eval/metrics.py`. See docs/STACK.md.
4. Current exact Next.js and USWDS major versions at `uv`/`npm` lock time (Next.js 15.x and USWDS 3.x assumed).
5. Live OFAC→GLEIF match yield beyond the seeded case (W1-3) — ship seeded-only if thin.
6. OFAC SLS namespace/schema stability at fetch time (W1-4).
