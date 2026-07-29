# Data Source Table + Exclusion List

> Decomposed from CLAUDE.md §9 (2026-07-28). This table is the ONLY permitted fetch set (NO-RESTRICTED-DATA INVARIANT, CLAUDE.md §2, invariant 3); `reglens/ingest/allowlist.py` enforces it at runtime.

| Source | Endpoint (verified) | Auth | Limits | Cadence | License | PII/legal status |
|---|---|---|---|---|---|---|
| Federal Register API v1 | `https://www.federalregister.gov/api/v1/documents.json` | None | per_page ≤ 1000; only first 2000 results paginable (use date filters); no key/rate limit for reasonable use | Business days | U.S. Gov public domain | Public rulemaking; no PII concern |
| eCFR Title 31 (point-in-time) | eCFR REST API (`https://www.ecfr.gov/...`, see eCFR Developer Resources) + bulk XML `https://www.govinfo.gov/bulkdata/ECFR/title-31` (set Accept header; 406 otherwise) | None | Polite throttle | eCFR daily; govinfo periodic (T31 last built 2026-05-07 per bulk listing) | U.S. Gov; eCFR is an unofficial editorial compilation (only PDF/Text CFR on govinfo are legally official) | Public regulation |
| OFAC Sanctions List Service | `https://sanctionslistservice.ofac.treas.gov/...` files `SDN_ADVANCED.XML`, `CONS_ADVANCED.XML`, `SDN.CSV`, `CONS_PRIM.CSV`; XML namespace `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML` | None but **User-Agent header REQUIRED (403 without)** | GET only; weekly/bi-weekly updates | On designation | U.S. Gov public | Names of designated persons — public by law; still handle carefully |
| GLEIF Golden Copy / Concatenated (Level 1 + Level 2 RR-CDF 2.1) | `https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy` + concatenated-files download | None | Full-file + delta files | Golden Copy 3×/day; concatenated daily | Open data (free redistribution) | Corporate reference data; no private-individual PII |
| OpenSanctions (enrichment/join) | Bulk download, no key; datasets `us_ofac_sdn`, `securities`, `ext_gleif` | None for bulk | Daily updates | Daily (4×/day upstream) | **CC-BY-NC 4.0 (non-commercial)** — attribution required | Aggregated public sanctions data |
| Treasury Fiscal Data (optional secondary demo) | `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny` etc. | None | No documented limit; throttle | Daily/monthly | U.S. Gov public | No PII |

## EXTEND-OGC01 extension sources (added 2026-07-28)

| Source | Endpoint (verified) | Auth | License | Notes |
|---|---|---|---|---|
| U.S. Code (OLRC USLM XML) | `https://uscode.house.gov/download/releasepoints/us/pl/119/102/xml_usc{NN}@119-102.zip` (pinned release point PL 119-102, 2026-07-12) | None | U.S. Gov public domain | Full title zips cached locally (gitignored); only cited-section XML fragments are snapshotted into `data/raw/` |
| Document Drafting Handbook | `https://www.archives.gov/files/federal-register/write/handbook/ddh.pdf` (Aug 2018 ed., rev. 2.2, mandatory as of 2025-06-09) | None | U.S. Gov public | Basis for the draft-skeleton template + conformance rules |
| reginfo.gov E.O. 14192 accounting | `https://www.reginfo.gov/public/pdf/eo14192/Final_Accounting_for_Fiscal_Year_2025_under_EO_14192.pdf`, `.../Accounting_Methods_under_EO_14192.pdf` | None | U.S. Gov public | PDFs only (no xlsx workbook exists); Table 1 field names source the offset-accounting stub |

Explicitly forbidden as dependencies (EXTEND-OGC01 §2): CourtListener API (rate-limited; membership breaks zero-cost), QuantGov/RegData datasets (cited as prior art only), anything requiring an api.data.gov key.

**EXCLUSION LIST (never fetch/store/synthesize):** BSA/SAR data; FinCEN Beneficial Ownership Information (also largely inactive for U.S. companies after the 2025-03-26 interim final rule); taxpayer data; PII about private individuals; anything behind authentication or paywalls; any Vixio employer data or work product. Enforced by `ingest/allowlist.py` (only the six sources above are fetchable) + Semgrep/gitleaks scans.
