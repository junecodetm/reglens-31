# RegLens-31

RegLens-31 is a zero-cost, auditable prototype that ingests public U.S. federal regulatory material and extracts structured, individually source-verified obligations. It combines local-only extraction, statutory-authority classification, two-sided *Loper Bright* marker retrieval, parameterized rule drafting, review memoranda, evaluation with uncertainty intervals, and governance controls. The project is an independent working mockup aligned to Treasury AI use case OGC-01, not the OGC-01 system; it uses no Treasury-internal information, makes no deregulatory recommendation, and draws no legal conclusion.

**Live site:** [https://reglens-31.pages.dev](https://reglens-31.pages.dev)

The deployed site is a pre-computed static export. Its core pages and read API require no backend, account, or API key.

## Quickstart

```sh
just setup  # install Python/web dependencies and the pinned local model
just demo   # serve the committed static export
```

No API key is required. After the one-time setup downloads, `just demo` operates fully offline.

Live drafting is optional. To enable the Groq-backed drafting workflow, place the following values in the gitignored `.env` file:

```dotenv
REGLENS_GROQ_API_KEY=your_key
REGLENS_DRAFT_PROVIDER=groq
```

Extraction remains local-only. The pinned Groq free-tier model is limited to the short draft and memorandum narrative stages and the optional live drafting endpoint.

## Capabilities

- **Provenance-gated extraction.** A schema-constrained local model proposes obligations with verbatim quotations. `reglens/provenance.py` accepts a claim only when the normalized quotation is an exact source substring and maps it back to exact display offsets. Unverifiable claims are rejected, counted, and exposed for review.

- **Statutory-authority classification.** `reglens/authority/` resolves cited U.S.C. sections against pinned OLRC USLM text and classifies the operative grant as mandatory, discretionary, silent, or unresolved. Classification spans are verified against the source; unresolved or unverifiable citations fail closed.

- **Two-sided *Loper Bright* markers.** `reglens/grounding/` retrieves deference-reliance and grounding-strength markers with equal weight. Counts, density bands, and rule facts describe text for attorney review; they do not predict validity or judicial outcomes.

- **Review memoranda.** `reglens/memo.py` assembles deterministic evidence for each in-scope part and adds a clearly labeled model-generated narrative. Narrative gates require both marker families and reject quotations, numerals, and fabrication patterns; deterministic evidence remains available if prose is rejected.

- **Parameterized drafting.** The drafting grid covers five parts crossed with NPRM and final-rule formats. Every committed draft passes structural, placeholder-integrity, quotation, fabrication, authority, and set-out checks. The optional `/api/draft` endpoint accepts a part, rule type, and bounded policy objective, applies an in-browser gate subset, and falls back to the committed conformance-gated draft when generation is unavailable or rate-limited.

- **Evaluation with uncertainty.** `reglens/eval/` reports provision-level precision, recall, and F1 with 95% Wilson and document-clustered bootstrap intervals, ICC/design effect, citation fidelity, and Cohen's kappa. Results carry the label **Provisional — machine-proposed labels, human-adjudicated: 0/251** until adjudication changes the versioned count. Reported kappa is cross-model agreement between two different frontier models applying the written guidelines, never human inter-annotator agreement.

- **Static read API.** The same exported artifacts used by the site are published as typed JSON under [`/api/v1/`](https://reglens-31.pages.dev/api/v1/index.json), with a generated [OpenAPI 3.1 document](https://reglens-31.pages.dev/api/v1/openapi.json). The API includes corpus metadata, documents, materialized claim pages, CFR sections, currency data, and evaluation metrics.

- **Review interface.** The site provides source-span inspection, accepted/rejected evidence, filters for obligation type and affected party, free-text filtering, authority cross-references, review signals, memorandum panels, corpus search, and eCFR currency information.

## Operating boundaries

- The corpus contains every Federal Register final rule identified by the stated CFR-index rule for the five in-scope parts, subject to the documented pre-1994 metadata limitation. `reglens/corpus.py` defines the local extraction sample as the five part texts and in-scope Federal Register documents published in 2026. Completion of that sample and regeneration of its derived artifacts are submission gates in [docs/CHECKLIST.md](docs/CHECKLIST.md).

- The extraction contract reads the five CFR part texts in full and caps Federal Register inputs at 80,000 characters for tractability. Completed records carry total and extracted character counts for display.

- Local-model extraction accuracy remains a material limitation. The provenance gate establishes a citation-fidelity floor but does not establish semantic correctness; the evaluation harness measures the remaining errors.

- Machine-proposed evaluation labels are not ground truth. Human adjudication is incomplete, and human inter-annotator agreement is not reported.

- Authority classes and marker bands are retrieval outputs, not legal determinations. The project does not perform judicial-outcome prediction, produce ranked repeal lists, or identify legal vulnerability.

- The deployed corpus is a dated static snapshot. Currency reporting compares the five ingested parts with eCFR amendment data and does not measure Federal Register staleness or the legal significance of an amendment.

- Live draft output passes only the documented in-browser subset of the full conformance gate. It is labeled accordingly; failures and shared free-tier quota exhaustion return the committed, fully gated draft.

- The static API has no runtime query engine. Filtering and pagination are materialized during export.

- The OFAC 50% ownership graph is de-scoped. Its entity-resolution design and limitations remain in `docs/ENTITY_RESOLUTION.md`; the project is not a sanctions-screening system.

## Data sources and licensing

Runtime allow-list enforcement limits ingestion to the public sources documented in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md), including Federal Register, eCFR, OLRC U.S. Code release points, and pinned federal drafting and governance references.

Code is licensed under [Apache-2.0](LICENSE). [DATA_LICENSE.md](DATA_LICENSE.md) records source provenance and data terms. OpenSanctions data is not used in this build; its CC-BY-NC 4.0 non-commercial restriction and attribution requirement remain documented because the de-scoped entity-resolution design evaluates it as a possible source.

## Documentation

- [Architecture and data flow](docs/ARCHITECTURE.md)
- [Command surface](docs/COMMANDS.md)
- [Security and threat model](docs/SECURITY.md)
- [Technology stack and zero-cost controls](docs/STACK.md)
- [Data sources and exclusions](docs/DATA_SOURCES.md)
- [Evaluation methodology](docs/EVALUATION.md)
- [Annotation and adjudication protocol](docs/ANNOTATION_GUIDELINES.md)
- [Governance mapping](docs/GOVERNANCE.md)
- [OGC-01 alignment and framing constraints](docs/OGC01-ALIGNMENT.md)
- [Blueprint realization map](docs/BLUEPRINT-ALIGNMENT.md)
- [M-25-21 crosswalk](docs/M25-21-CROSSWALK.md)
- [Submission checklist and scope decisions](docs/CHECKLIST.md)
- [Contribution workflow](CONTRIBUTING.md)

## Disclaimer

> This is an independent, personal project. It is not affiliated with, endorsed by, or an official product of the U.S. Department of the Treasury or any government agency. It uses only public data and does not use Treasury names, seals, or symbols to imply affiliation (31 U.S.C. §333). It is an assistive prototype, not legal or compliance advice; verify all outputs against primary sources.
