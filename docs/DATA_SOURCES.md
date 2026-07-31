# Data sources and exclusions

`reglens/ingest/allowlist.py` enforces the permitted fetch set at runtime under
the NO-RESTRICTED-DATA invariant.

| Source | Endpoint | Auth | Limits | Cadence | License | PII/legal status |
|---|---|---|---|---|---|---|
| Federal Register API v1 | `https://www.federalregister.gov/api/v1/documents.json` | None | `per_page` ≤ 1000; only the first 2000 results are paginable, so corpus ingestion uses date filters | Business days | U.S. Government public domain | Public rulemaking; no private PII |
| eCFR Title 31 (point in time) | eCFR REST API (`https://www.ecfr.gov/...`) and govinfo bulk XML at `https://www.govinfo.gov/bulkdata/ECFR/title-31` (the bulk endpoint requires an `Accept` header) | None | Polite throttle | eCFR daily; govinfo periodic | U.S. Government work; eCFR is an unofficial editorial compilation, and only the PDF and text CFR on govinfo are legally official | Public regulation |
| OFAC Sanctions List Service | `https://sanctionslistservice.ofac.treas.gov/...` files `SDN_ADVANCED.XML`, `CONS_ADVANCED.XML`, `SDN.CSV`, and `CONS_PRIM.CSV`; XML namespace `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML` | None; **User-Agent header required** (requests without it return 403) | GET only | On designation | U.S. Government public data | Names of designated persons are public by law but require careful handling |
| GLEIF Golden Copy / Concatenated files (Level 1 and Level 2 RR-CDF 2.1) | `https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy` and concatenated-file download | None | Full and delta files | Golden Copy three times daily; concatenated file daily | Open data with redistribution permitted | Corporate reference data; no private-individual PII |
| OpenSanctions (enrichment/join) | Bulk datasets `us_ofac_sdn`, `securities`, and `ext_gleif` | None for bulk | Daily updates | Upstream updates four times daily | **CC-BY-NC 4.0 (non-commercial)** — attribution required | Aggregated public sanctions data |
| Treasury Fiscal Data (optional secondary demonstration) | `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny` and related endpoints | None | No documented limit; requests are throttled | Daily or monthly, by dataset | U.S. Government public domain | No PII |

## Corpus inclusion rule

`reglens/corpus.py` defines the corpus as Title 31 parts 50, 223, 285, 356,
and 501. `reglens.ingest.federal_register.corpus_document_numbers` returns every
final rule that the Federal Register CFR index attributes to an in-scope part,
with pagination and de-duplication. The corresponding ingestion command is
documented in [docs/COMMANDS.md](COMMANDS.md).

The rule selects 132 unique final rules: 31 for part 50, 2 for part 223, 32 for
part 285, 32 for part 356, and 37 for part 501. Two rules amend more than one
in-scope part. Raw text was available for all 132 rules. The committed corpus
also retains 20 Federal Register documents identified through citation
traversal that the CFR index does not tag, for 152 unique Federal Register
documents in total.

The Federal Register CFR index depends on metadata that identifies affected CFR
parts. It therefore cannot reach every older rule that may have affected these
parts. The corpus is complete only with respect to the executable inclusion
rule. Proposed rules and notices are outside the rule-selected scope.

## Extraction-sample rule

Ingestion and extraction have separate executable boundaries.
`reglens.corpus.in_extraction_sample` selects the five in-scope 31 CFR part
texts and every committed Federal Register document published in
`EXTRACTION_YEAR` (2026). This selects 25 of the 157 documents paired under
`data/raw/`. All 157 documents are ingested, content-addressed, and committed.
The full-corpus extraction option is documented in
[docs/COMMANDS.md](COMMANDS.md).

The published denominator is the full committed set: 152 Federal Register
documents plus 5 part texts. The 20 citation-derived documents count because
they are available to the extraction pipeline. The default extraction command
recreates only the defined sample, preventing a full-corpus run from changing
the published sample coverage.

Inference runs on one laptop. A full-corpus pass requires hours of local compute
and must be repeated after a model, prompt, runtime, or chunking change. The
executable sampling boundary makes this limitation reproducible and testable.
`tests/test_corpus.py` verifies that persisted claims match the rule-selected
sample. The site reports `documents_extracted` against `documents_in_scope` on
the Overview, the obligations page, and every footer.

The five part texts are extracted in full. Federal Register documents are
capped at 80,000 characters; one source document exceeds 1.3 million
characters. Each record publishes `total_chars` and `extracted_chars` so the
shortfall remains visible.

## OGC-01-aligned supporting sources

These sources support the retrieval and drafting functions subject to the
[Framing constraints](OGC01-ALIGNMENT.md#framing-constraints--non-negotiable).

| Source | Endpoint | Auth | License | Use |
|---|---|---|---|---|
| U.S. Code (OLRC USLM XML) | `https://uscode.house.gov/download/releasepoints/us/pl/119/102/xml_usc{NN}@119-102.zip` (pinned release point PL 119-102, 2026-07-12) | None | U.S. Government public domain | Full title archives are cached locally and gitignored; only cited-section XML fragments are snapshotted under `data/raw/` |
| Document Drafting Handbook | `https://www.archives.gov/files/federal-register/write/handbook/ddh.pdf` (August 2018 edition, revision 2.2, mandatory beginning 2025-06-09) | None | U.S. Government public data | Basis for draft-skeleton templates and conformance rules |
| reginfo.gov E.O. 14192 accounting | `https://www.reginfo.gov/public/pdf/eo14192/Final_Accounting_for_Fiscal_Year_2025_under_EO_14192.pdf` and `.../Accounting_Methods_under_EO_14192.pdf` | None | U.S. Government public data | The sources are PDF-only; Table 1 field names define the offset-accounting stub |

## Reference snapshot

| Source | Endpoint | Auth | License | Use |
|---|---|---|---|---|
| Treasury AI Use Case Inventory | `https://home.treasury.gov/system/files/136/Treasury-AI-Use-Case-Inventory.csv` (landing page: `https://home.treasury.gov/data/ai_inventory`) | None; a User-Agent header is sent | U.S. Government work (17 U.S.C. §105) | Pinned, content-addressed reference for the site's OGC-01 framing; `reglens/store/export_web.py` reads only the committed snapshot. This file is not a pipeline extraction input. |

CourtListener, QuantGov/RegData datasets, and sources requiring an
`api.data.gov` key are excluded dependencies. QuantGov/RegData may be cited as
prior art but are not ingested. The final capability scope and de-scopes are
recorded in [docs/CHECKLIST.md](CHECKLIST.md).

OpenSanctions remains allow-listed only for the de-scoped ownership-graph
capability and is not ingested by RegLens-31. Any future use remains subject to
**CC-BY-NC 4.0 (non-commercial)** and requires attribution.

## Exclusion list

The system never fetches, stores, or synthesizes BSA/SAR data; FinCEN Beneficial
Ownership Information; taxpayer data; PII about private individuals; data
behind authentication or paywalls; or Vixio employer data or work product.
`reglens/ingest/allowlist.py` enforces source access, and Semgrep and gitleaks
provide additional repository checks.
