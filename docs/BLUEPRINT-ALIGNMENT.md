# Blueprint Alignment — "Treasury GenAI Architecture Blueprint" → RegLens-31

This document maps each feature in `docs/treasury-genai-architecture-blueprint.md`
to its implementation, a neutral zero-cost equivalent, or an explicit exclusion.
Repository constraints govern any conflict with the blueprint: `CLAUDE.md` §2,
the "Framing constraints" section of `docs/OGC01-ALIGNMENT.md`, the zero-cost
static-export architecture, and the data-source allow-list. Scope decisions are
recorded in `docs/CHECKLIST.md`.

## Implementation dispositions

- **Implemented:** present in the repository and static export.
- **Neutral equivalent:** the blueprint's underlying intent is served through the
  project's retrieval-only presentation without legal conclusions.
- **Excluded:** outside the defined scope or inconsistent with a controlling constraint.

## §1 Foundational architecture and ingestion

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| USLM XML consumption from GPO/OLRC | Implemented | `reglens/ingest/uscode.py` consumes the pinned OLRC release point (PL 119-102), preserves USLM `identifier` attributes, and uses a digest-verified replay cache. Title 31 text comes from govinfo and eCFR XML. Deterministic replay is used instead of automated synchronization because it provides stronger reproducibility. |
| Ingestion scope: IRC (26 U.S.C.), CFR Titles 26+31, APA, daily Federal Register | Partially implemented; broader scope excluded | The corpus covers five 31 CFR parts (50, 223, 285, 356, and 501) and their cited U.S. Code sections across 13 titles. Title 26 sections appear only when cited as authority. Whole-title IRC and CFR Title 26 ingestion exceed the laptop-local prototype scope, although the pipeline is title-agnostic. |
| Hierarchical "Venetian Blind" navigation tree | Implemented | The browse view provides Title 31 → part → section navigation over the ingested parts and connects each section to its source text. Paragraph-level navigation is not implemented. |
| Temporal versioning toggle (`@temporalId`) | Excluded | Point-in-time pinning uses eCFR snapshots dated 2026-07-01 for the claims corpus and 2026-07-27 for the authority corpus, with the snapshot date displayed in the interface. The five parts are textually identical across those snapshots, so a comparison view would contain no changes. |
| "Zero-hallucination hybrid search" (dense vectors + BM25 + chat) | Neutral equivalent: lexical search | A precomputed static index supports client-side exact-term search across claims, U.S. Code sections, CFR sections, and drafts. It provides neither semantic ranking nor chat. Dense embeddings and chat would require a live service or large in-browser models, contrary to the static-export constraint. Each rendered claim links to its primary source. |

## §2 Modality A — "Statutory Audit & Optimization Engine"

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| "Vulnerability Matrix" / batch viability scan under *Loper Bright* | Excluded by framing constraints | The repository does not produce vulnerability findings, "at risk" labels, repeal-candidate lists, or judicial-outcome predictions. The neutral equivalent classifies operative grants as mandatory, discretionary, silent, or unresolved and supports each classification with a gate-verified verbatim span. |
| Red highlighting of delegatory/subjective terms | Neutral equivalent; red/green findings excluded | Two-sided grounding-marker retrieval presents deference-reliance and grounding-strength marker families with equal visual weight. It does not apply red/green validity or risk semantics. |
| Statutory Delegation Tracer (rule → authorizing U.S. Code, split view) | Implemented | The authority view parses each part's authority citation into typed citations. Resolved sections load pinned USLM text and highlight the classified grant span. The classification describes operative text and does not adjudicate validity. |
| Deference scoring (probabilistic risk) + "Deregulatory Target Report" | Excluded by framing constraints | The system produces neither probabilistic judicial-outcome scores nor deregulatory target lists. Textual-marker density bands report marker counts per 1,000 words, which describe the text rather than litigation risk. |

## §2 Modality B — Generative drafting engine

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| DDH/OFR-conformant NPRM + Final Rule outputs | Implemented | `reglens/draft/` provides Document Drafting Handbook skeletons based on the snapshotted August 2018 edition, revision 2.2. Preamble captions appear in the required order, required analyses remain visible as `[PLACEHOLDER — attorney to complete]` blocks, and a fail-closed conformance checker prevents publication of rejected drafts. |
| Amendatory-instruction generation (add / revise / remove-and-reserve) | Implemented | Each skeleton demonstrates all three OFR verb forms with placeholder designations. The conformance checker verifies their presence and grammar. The system does not propose a substantive amendment; an attorney must supply the substance. |
| Bureau-specific templating (IRS TDs, FinCEN/31 CFR Ch. X) | Excluded (scope + §333) | Chapter X expansion is forbidden by the owner-pinned scope; the skeleton's AGENCY caption is deliberately a placeholder and never names Treasury or a bureau (31 U.S.C. §333 non-affiliation invariant). |
| Generative supplementary information, locked out of fabricating authorities | Implemented | The committed grid's labeled narrative fields use the pinned Groq free-tier `openai/gpt-oss-120b` model at temperature 0. Extraction remains local-only. The fabrication scan rejects RIN, docket, dollar, phone, email, date, and URL patterns, and the verbatim-quote gate rejects the entire draft when a check fails. |

## §2 Modality C — Dependency mapping

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| Interactive legal knowledge graph (Memgraph) | Neutral equivalent: static cross-references | A live graph database is inconsistent with the precomputed static architecture. The cross-reference view reads `authority.json` and presents each CFR part with its cited U.S. Code sections in both directions as accessible lists rather than a canvas. |
| "Domino Effect Simulation" (3-degree impact traversal) | Excluded by framing constraints and data scope | Regulatory-impact simulation is predictive, and a meaningful traversal would require corpus-wide reference data beyond the five in-scope parts. The cross-reference view states this limitation. |
| Cross-agency conflict alerts (FinCEN/OCC definitions) | Excluded (data allow-list) | The data allow-list excludes the required FinCEN and OCC corpora and BSA materials. |

## §2 Modality D — APA compliance

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| Public-comment clustering via Regulations.gov API v4 | Excluded (zero-cost allow-list) | Regulations.gov v4 requires an api.data.gov key — explicitly forbidden in `docs/DATA_SOURCES.md`. No comment data is ingested. |
| Preamble response generator (counter-argument ↔ response) | Excluded | This feature depends on excluded comment ingestion and could fabricate agency positions. It is inconsistent with the framing and non-affiliation constraints. |
| Final APA checklist (authority citation, basis-and-purpose, comment period, PRA/RFA) | Implemented | The conformance checker applies named structural checks for authority-citation presence, basis-and-purpose elements, comment-period or effective-date references, and required analyses. The interface labels the checklist "structural presence only; not a legal-sufficiency determination." |

## §3 Human-in-the-loop governance

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| Attribution workspace (raw AI output vs attorney edit, immutable trail) | Neutral equivalent | Model-generated narrative fields are labeled inline `[model-generated]`; all other content is a deterministic template or gate-verified quotation. The static export has no attorney-editing surface or edit-diff pane. The per-draft dossier is the available audit trail. |
| Model & system dossier export | Implemented | Each draft includes a provenance dossier containing the model tag, decoding parameters (temperature 0, pinned seed, and context and prediction limits), and SHA-256 values for the system prompt, user prompts, and source input. The committed snapshots support reproducibility checks. |
| Form 450 / RBAC conflict-of-interest lockout | Excluded (non-goals + restricted data) | The project is single-user, unauthenticated, and stores no user data (`CLAUDE.md` non-goals). OGE Form 450 databases contain confidential financial-disclosure PII and are excluded by the restricted-data policy. |

## §4 System foundation

| Blueprint feature | Disposition | Implementation or rationale |
|---|---|---|
| Air-gapped local open-weights model | Implemented | `qwen3:8b` runs through Ollama on the local machine at temperature 0 with a pinned tag; `local`-only mode provides the air-gap posture. Fine-tuning is outside scope, and the blueprint's 70B model does not fit the 16 GB target machine. |
| pgvector + sentence-transformer semantic search | Excluded (stack constraint) | PostgreSQL hosting conflicts with the zero-cost architecture, and semantic search would require live compute. The static lexical index is the supported equivalent. |
| Memgraph real-time graph analytics | Excluded (zero-infra) | See Modality C. |
| LangChain / LlamaIndex unified agentic dashboard | Excluded (stack decision) | The pipeline uses typed Python without an orchestration framework to keep execution paths directly auditable (`docs/STACK.md`). The static multi-page interface provides one portal for the supported capabilities. |

## Summary

The implementation covers ingestion, delegation tracing, drafting, local model
execution, lexical search, hierarchical browsing, static cross-references, amendatory
verb forms, an APA structural checklist, and per-draft provenance dossiers. Exclusions
follow the framing constraints, zero-cost static-export architecture, data-source
allow-list, or documented scope. These exclusions include vulnerability scoring,
judicial-outcome prediction, deregulatory target lists, live graph infrastructure,
comment ingestion, and whole-title expansion.
