# RegLens-31

A solo-built, zero-cost, auditable prototype that ingests U.S. federal regulatory and sanctions data and extracts structured, individually source-verified regulatory obligations — with a real evaluation harness and governance-as-code. Every extracted claim carries a verbatim source span; a deterministic, fail-closed provenance gate rejects any claim it cannot prove against the primary source. Inference runs entirely locally on Apple Silicon: no third-party AI data egress.

<!-- README skeleton per CLAUDE.md §16. TODO markers are filled in during the build phases (docs/BUILD_PLAN.md). -->

## Demo

**Zero-friction path:** `just demo` — no API key, fully offline, seeded data; opens the static site.

<!-- TODO(Phase 2): live Cloudflare Pages URL -->
<!-- TODO(Phase 2): screenshots -->

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the repository structure and data-flow diagram.

## Setup & run

<!-- TODO(Phase 0): uv sync / just setup instructions once pyproject.toml exists -->

```
just setup   # uv sync, install pre-commit, pull local model
just demo    # offline demo on seeded data
```

Full command surface: [docs/COMMANDS.md](docs/COMMANDS.md).

## Approach, Tools, and Assumptions

<!-- Required by announcement 26-DO-12891471-DH. TODO(Phase 5): final prose. Interim pointers: -->

- Approach: provenance-gated obligation extraction, local-first inference, evaluation with honest confidence intervals — [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/EVALUATION.md](docs/EVALUATION.md), [docs/GOVERNANCE.md](docs/GOVERNANCE.md)
- Tools: [docs/STACK.md](docs/STACK.md) (audited zero-cost stack)
- Assumptions & week-one falsification tests: [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md)

## Honest limitations

- Entity-resolution coverage is partial: OFAC publishes no LEIs; most SDN records are not LEI-joinable; GLEIF Level 2 records accounting consolidation, a proxy for — not identical to — 50% Rule ownership. See [docs/ENTITY_RESOLUTION.md](docs/ENTITY_RESOLUTION.md).
- OpenSanctions data is CC-BY-NC 4.0 (non-commercial) — fine for this portfolio artifact; a production deployment would require a commercial license.
- Prototype scope: assistive, human-in-the-loop; not a sanctions-screening product, not legal advice.
- Local-model whole-document extraction accuracy is a known hard problem — exactly why the provenance gate and eval harness exist.

## Demo staleness

<!-- TODO(Phase 5): dated snapshot note + "as of" banner + link to governance/monitoring_plan.md refresh/retirement policy -->

The deployed demo is a pre-computed static export of a dated data snapshot; it does not update live.

## Disclaimer

> This is an independent, personal project. It is not affiliated with, endorsed by, or an official product of the U.S. Department of the Treasury or any government agency. It uses only public data and does not use Treasury names, seals, or symbols to imply affiliation (31 U.S.C. §333). It is an assistive prototype, not legal or compliance advice; verify all outputs against primary sources.
