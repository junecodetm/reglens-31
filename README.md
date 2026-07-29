# RegLens-31

A solo-built, zero-cost, auditable prototype that ingests U.S. federal regulatory data and extracts structured, individually source-verified regulatory obligations — with a real evaluation harness and governance-as-code. Every extracted claim carries a verbatim source span; a deterministic, fail-closed provenance gate rejects any claim it cannot prove against the primary source. Inference runs entirely locally on Apple Silicon: no third-party AI data egress.

**Live demo:** https://reglens-31.pages.dev — a pre-computed static export; loads cold with no backend and no API key.

## Demo

**Zero-friction path (clean clone):**

```
just setup   # uv sync + npm install + pull the pinned local model (network, one time)
just demo    # serve the pre-built static site locally — offline, no API key
```

The demo makes no network calls: all data ships as static assets. `just extract` re-runs the local pipeline end-to-end (requires Ollama with `qwen3:8b`).

## What the reviewer is looking at

1. **Obligation extraction with a fail-closed provenance gate** (`reglens/provenance.py`). A local model (qwen3:8b via Ollama, temperature 0, JSON-schema-constrained) proposes obligations with verbatim quotes; a deterministic normalizer (character-wise NFKC + whitespace collapse, documented in the module) accepts a claim only if its quote is an exact substring of the source — and maps it back to exact highlight offsets. Anything unverifiable is **rejected and counted, never hidden**: the UI banner shows the rejection count, and a transparency section lists every rejected claim with its reason.
2. **Evaluation with honest uncertainty** (`reglens/eval/`). Provision-level P/R/F1 against a 251-provision gold set with 95% Wilson intervals, clustered (by-document) bootstrap intervals, ICC/design-effect-adjusted effective n, and Cohen's kappa. Gold labels are machine-proposed and explicitly labeled **Provisional** until human-adjudicated (`docs/ADJUDICATE.md`); the adjudicated count is wired to the versioned JSONL, so the label restates itself as adjudication proceeds. A CI gate re-runs the eval from committed fixtures at $0 and fails on F1 regression or any citation-fidelity defect.
3. **Security & governance as code**: SHA-pinned least-privilege workflows, CodeQL + semgrep + gitleaks + pip-audit + osv-scanner, CycloneDX SBOM, a runtime data-source allow-list, and a zero-cost invariant checker that fails the build if a non-allow-listed dependency, action, or external host appears.
4. **OGC-01 extension — authority, grounding, drafting** (EXTEND-OGC01; mapped to Treasury AI use case OGC-01 "Regulatory Reform Tool" in [docs/OGC01-ALIGNMENT.md](docs/OGC01-ALIGNMENT.md)):
   - **Statutory authority linker** (`reglens/authority/`): each part's authority citation parsed with exact spans, every cited U.S.C. section resolved against a pinned OLRC USLM release point, and the operative grant classified {mandatory, discretionary, silent, unresolved} by a published deterministic pattern table — the verbatim statutory verb phrase is gate-verified, unresolvable citations fail closed, and note/Pub. L./E.O. citations are a separate coverage category.
   - **Two-sided grounding signal** (`reglens/grounding/`): exact gate-verified marker spans in two equal-weight families (deference-reliance AND grounding-strength) plus neutral per-rule facts; bands are textual-marker density only — retrieval, never prediction.
   - **Draft rule skeletons** (`reglens/draft/`): DDH-conformant NPRM/final skeletons — deterministic structure, visible `[PLACEHOLDER — attorney to complete]` blocks for every required analysis, a labeled model-generated narrative, and a conformance checker (fabrication scan + quote gate) that rejects rather than caveats.
   - Governance crosswalk: [docs/M25-21-CROSSWALK.md](docs/M25-21-CROSSWALK.md) (OMB M-25-21 §4(b) minimum practices + NIST AI 600-1 Confabulation/Information Integrity).

## Setup & run

```
just setup       # uv sync, web npm install, ollama pull qwen3:8b
just ingest      # snapshot Federal Register + eCFR Title 31 sources (allow-listed only)
just extract     # local extraction + provenance gate -> data/processed/claims.json
just authority   # authority citations -> USLM resolution -> classification
just grounding   # two-sided grounding-marker retrieval
just draft       # DDH rule skeletons + conformance gates
just eval        # metrics + Wilson/bootstrap CIs (core + OGC-01) -> web/public/data/
just build-web   # export data + Next.js static export -> web/out
just demo        # serve web/out locally, fully offline
just ci          # lint + types + tests + zero-cost check
```

Full command surface: [docs/COMMANDS.md](docs/COMMANDS.md).

## Approach, tools, and assumptions

- **Approach:** provenance-gated extraction as an auditable correctness floor (citation grounding is a commodity; running the check deterministically, fail-closed, and locally is the point), local-first inference as a data-sovereignty posture, and evaluation/governance as first-class deliverables. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/EVALUATION.md](docs/EVALUATION.md), [docs/GOVERNANCE.md](docs/GOVERNANCE.md), [docs/SECURITY.md](docs/SECURITY.md).
- **Tools:** Python 3.13 + uv + ruff + pyright strict + pydantic v2; Ollama (qwen3:8b, temp 0, JSON-schema `format`); Next.js 15 static export + react-uswds; GitHub Actions + Cloudflare Pages (free tiers, no card anywhere). Audited stack: [docs/STACK.md](docs/STACK.md).
- **Assumptions & falsification tests:** [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md). Deviations are recorded in [docs/PROGRESS.md](docs/PROGRESS.md).
- **Determinism:** content-addressed raw snapshots (SHA-256), pinned model tag, temperature 0, fixed seed, recorded prompt/input hashes; re-running a step on the same input SHA is a no-op.

## Honest limitations

- **Gold labels are provisional.** Machine-proposed, human adjudication in progress; every metric carries the label until done. The reported kappa is agreement between two different frontier models (frozen proposal passes) applying the written guidelines — not human inter-annotator agreement, which awaits adjudication.
- **Extraction coverage is bounded.** Very long documents are extracted up to a disclosed per-document cap; `total_chars`/`extracted_chars` are recorded per document.
- **Local-model extraction accuracy is a known hard problem** — which is exactly why the provenance gate (precision floor) and the eval harness (honest measurement) exist.
- Prototype scope: assistive, human-in-the-loop; not a sanctions-screening product, not legal advice.
- The OFAC 50% Rule ownership-graph module was de-scoped from this build (see docs/PROGRESS.md); the entity-resolution analysis and its caveats remain documented in [docs/ENTITY_RESOLUTION.md](docs/ENTITY_RESOLUTION.md).
- **The OGC-01 extension makes no legal conclusions and predicts nothing.** Classification is deterministic pattern retrieval with measured accuracy; marker bands are phrase-frequency facts; skeletons contain structure, not substance. The full limitations list — the most important section for that work — is [docs/OGC01-ALIGNMENT.md](docs/OGC01-ALIGNMENT.md).

## Demo staleness

The deployed demo is a pre-computed static export of a dated snapshot (the "data as of" date is shown in the site footer); it does not update live. Refresh/retirement policy: `governance/monitoring_plan.md`.

## Data sources & licensing

Only the allow-listed public sources in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) are ever fetched (enforced at runtime by `reglens/ingest/allowlist.py`). This build uses the Federal Register API and eCFR Title 31 (U.S. Government public domain). Code is Apache-2.0 ([LICENSE](LICENSE)); data provenance and attribution: [DATA_LICENSE.md](DATA_LICENSE.md).

## Disclaimer

> This is an independent, personal project. It is not affiliated with, endorsed by, or an official product of the U.S. Department of the Treasury or any government agency. It uses only public data and does not use Treasury names, seals, or symbols to imply affiliation (31 U.S.C. §333). It is an assistive prototype, not legal or compliance advice; verify all outputs against primary sources.
