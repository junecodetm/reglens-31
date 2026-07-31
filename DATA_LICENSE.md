# Data Provenance & Licensing

Code in this repository is licensed under Apache-2.0; see [LICENSE](LICENSE). Data artifacts under `data/` and `web/public/data/` derive exclusively from the included public sources identified below. Excluded sources are listed for licensing clarity.

| Source | Used for | License / status |
|---|---|---|
| Federal Register API v1 (`www.federalregister.gov`) | Rule text + metadata snapshots | U.S. Government public domain |
| eCFR versioner API (`www.ecfr.gov`), Title 31 | Point-in-time regulation text | U.S. Government work; the eCFR is an unofficial editorial compilation — only the PDF/Text CFR on govinfo is legally official |
| U.S. Code USLM XML (`uscode.house.gov`), release point PL 119-102 | Cited-section statutory text for the authority linker | U.S. Government (OLRC) public domain |
| Document Drafting Handbook (`www.archives.gov`), Aug 2018 ed. rev. 2.2 | Provenance for the draft-skeleton template + conformance rules | U.S. Government (NARA) public |
| reginfo.gov E.O. 14192 accounting PDFs | Field names for non-substantive offset-accounting placeholders; the repository does not generate cost or savings estimates | U.S. Government public |
| Treasury AI Use Case Inventory CSV (`home.treasury.gov`) | Verbatim OGC-01 inventory row + corpus context for the site's "About this demonstration" section | U.S. Government work (17 U.S.C. §105) |
| OpenSanctions, OFAC SLS, GLEIF | Excluded; the ownership-graph module is outside the project scope, and no repository data artifact contains these sources | OpenSanctions is CC-BY-NC 4.0 with attribution if ever enabled; [docs/ENTITY_RESOLUTION.md](docs/ENTITY_RESOLUTION.md) records the retained design |

Every raw snapshot is content-addressed under `data/raw/<sha256>/` with a `manifest.json` recording source id, URL, fetch time, and hash. Derived claims record the model tag, prompt hash, and input hash that produced them.

No BSA/SAR data, FinCEN Beneficial Ownership Information, taxpayer data, private-individual PII, or authenticated or paywalled content is ingested. The runtime allow-list (`reglens/ingest/allowlist.py`) and CI scans enforce these exclusions.

## Non-OSS code dependency note

All code dependencies are OSS except **GSAP** (`gsap`, `@gsap/react`): free of
charge for this use under the [GreenSock Standard License](https://gsap.com/standard-license)
(public static-site use explicitly permitted; not an OSI license). Details in
`docs/STACK.md`.
