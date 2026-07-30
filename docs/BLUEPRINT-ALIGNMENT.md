# Blueprint Alignment — "Treasury GenAI Architecture Blueprint" → RegLens-31

> Written 2026-07-28. Maps every feature in `docs/Treasury GenAI Architecture Blueprint.md` (an
> aspirational enterprise product spec) to its realization in this repository, its neutral
> zero-cost equivalent, or its documented exclusion. Governing decision (owner-confirmed):
> **the committed invariants win** — CLAUDE.md §2, EXTEND-OGC01 §5 (neutrality framing),
> the zero-cost/static-export architecture, and the data-source allow-list override the
> blueprint wherever they conflict. This document is the honest reconciliation, in the same
> limitations-first spirit as `docs/OGC01-ALIGNMENT.md`.

## Reading the status column

- **Realized** — present in the shipped build.
- **Neutral equivalent** — the blueprint's underlying intent is served, but through the
  project's retrieval-only, no-legal-conclusions presentation (EXTEND-OGC01 §5).
- **Added (this pass)** — built during the blueprint-alignment pass, within the invariants.
- **Excluded** — deliberately not built; the reason names the controlling invariant.

## §1 Foundational architecture & ingestion

| Blueprint feature | Status | Where / why |
|---|---|---|
| USLM XML consumption from GPO/OLRC | Realized | `reglens/ingest/uscode.py` — pinned OLRC release point (PL 119-102), USLM `identifier` attrs, digest-verified replay cache; govinfo/eCFR XML for Title 31. Pinned deterministic replay rather than "automated sync": reproducibility is the stronger audit property. |
| Ingestion scope: IRC (26 U.S.C.), CFR Titles 26+31, APA, daily Federal Register | Excluded (scope) / partial | Scope is owner-pinned to five 31 CFR parts (50, 223, 285, 356, 501) plus their cited U.S. Code sections across 13 titles (Title 26 sections appear where cited as authority). Whole-title IRC/CFR-26 ingestion is out of scope for a solo laptop-local prototype; the pipeline is title-agnostic by construction. |
| Hierarchical "Venetian Blind" navigation tree | Added (this pass) | Browse section: Title 31 → part → section drill-down over the ingested parts, wired to the source-text panes. Depth stops at the section level — paragraph-level drill-down is not built. |
| Temporal versioning toggle (`@temporalId`) | Excluded (low value here) | Point-in-time pinning already exists (two dated eCFR snapshots: 2026-07-01 claims corpus, 2026-07-27 authority corpus; "as of" banner in the UI). A version-diff view was considered and skipped: the five parts are textually unchanged between the pinned dates, so a compare UI would render only "no change." Recorded here instead of shipped as an empty feature. |
| "Zero-hallucination hybrid search" (dense vectors + BM25 + chat) | Neutral equivalent, lexical only (this pass) | Client-side lexical search over the ingested corpus (claims, U.S. Code sections, CFR sections, drafts) with a precomputed static index. Labeled exactly what it is: exact-term lexical matching, no semantic ranking, no chat. Dense embeddings + a chat interface require a live backend or heavy in-browser models — excluded by the static-export invariant ("the reviewer never depends on a live backend"). Every rendered claim already links to its primary source, which is the substance behind the blueprint's "verifiable hyperlink" requirement. |

## §2 Modality A — "Statutory Audit & Optimization Engine"

| Blueprint feature | Status | Where / why |
|---|---|---|
| "Vulnerability Matrix" / batch viability scan under *Loper Bright* | Excluded (§5) | EXTEND-OGC01 §5 forbids exactly this framing ("vulnerability," "at risk," repeal-candidate lists, judicial-outcome prediction). The neutral equivalent ships: per-section operative-grant classification ({mandatory, discretionary, silent, unresolved}) with gate-verified verbatim spans, presented as retrieval, not prediction. |
| Red highlighting of delegatory/subjective terms | Excluded (§5) / neutral equivalent | No red/green semantics anywhere (§5). The two-sided grounding-marker retrieval highlights BOTH deference-reliance and grounding-strength marker families at equal weight, in neutral USWDS tokens. |
| Statutory Delegation Tracer (rule → authorizing U.S. Code, split view) | Realized | Authority section: each part's authority citation parses to typed cites; resolved sections load the pinned USLM text with the classified grant span highlighted. The blueprint's *binary safe/at-risk verdict* is excluded (§5: no legal conclusions) — classification describes operative text; it does not adjudicate validity. |
| Deference scoring (probabilistic risk) + "Deregulatory Target Report" | Excluded (§5) | Probabilistic judicial-outcome scores and deregulatory target lists are forbidden outputs. The shipped alternative is textual-marker density bands, defined in the UI as marker counts per 1,000 words — a property of the text, not a prediction about litigation. |

## §2 Modality B — Generative drafting engine

| Blueprint feature | Status | Where / why |
|---|---|---|
| DDH/OFR-conformant NPRM + Final Rule outputs | Realized | `reglens/draft/` — Document Drafting Handbook skeletons (Aug 2018 ed., rev. 2.2, snapshotted), preamble captions in required order, required analyses as visible `[PLACEHOLDER — attorney to complete]` blocks, fail-closed conformance checker; rejected drafts are never published. |
| Amendatory-instruction generation (add / revise / remove-and-reserve) | Added (this pass) | All three OFR verb forms are demonstrated in each skeleton with placeholder designations only, and the conformance checker verifies their presence and grammar. No real amendment is ever proposed — substance is the attorney's (Stage 3.3). |
| Bureau-specific templating (IRS TDs, FinCEN/31 CFR Ch. X) | Excluded (scope + §333) | Chapter X expansion is forbidden by the owner-pinned scope; the skeleton's AGENCY caption is deliberately a placeholder and never names Treasury or a bureau (31 U.S.C. §333 non-affiliation invariant). |
| Generative supplementary information, locked out of fabricating authorities | Realized | Local qwen3:8b at temperature 0 drafts only the labeled narrative fields; the fabrication scan (RIN/docket/dollar/phone/email/date/URL) and the verbatim-quote gate reject the whole draft on any hit. This is a stricter mechanism than the blueprint's "must pull from the RAG database." |

## §2 Modality C — Dependency mapping

| Blueprint feature | Status | Where / why |
|---|---|---|
| Interactive legal knowledge graph (Memgraph) | Excluded (zero-infra) / neutral equivalent (this pass) | A graph database is a live service; the invariant is a pre-computed static artifact. The shipped equivalent is a static cross-reference view over `authority.json`: each CFR part ↔ its cited U.S. Code sections, in both directions (which sections a part cites; which parts share a section). Rendered as accessible lists, not a canvas visualization. |
| "Domino Effect Simulation" (3-degree impact traversal) | Excluded (§5 + data scope) | Simulating regulatory impact is prediction, not retrieval; and a meaningful traversal needs corpus-wide reference data far beyond five parts. The cross-reference view states this limitation in its own copy. |
| Cross-agency conflict alerts (FinCEN/OCC definitions) | Excluded (data allow-list) | Requires ingesting FinCEN/OCC corpora — outside the owner-pinned scope, and adjacent to the NO-RESTRICTED-DATA exclusion list (BSA materials). |

## §2 Modality D — APA compliance

| Blueprint feature | Status | Where / why |
|---|---|---|
| Public-comment clustering via Regulations.gov API v4 | Excluded (zero-cost allow-list) | Regulations.gov v4 requires an api.data.gov key — explicitly forbidden in `docs/DATA_SOURCES.md`. No comment data is ingested. |
| Preamble response generator (counter-argument ↔ response) | Excluded | Depends on the excluded comment ingestion, and auto-generated agency responses to public comments would be fabricated agency positions — a §5/§333 defect. |
| Final APA checklist (authority citation, basis-and-purpose, comment period, PRA/RFA) | Added (this pass) | The conformance checker gains named structural checks — authority-citation presence, basis-and-purpose elements, comment-period/effective-date reference, plus the existing required-analyses check — rendered per draft in the UI as an APA procedural checklist, labeled "structural presence only; not a legal-sufficiency determination." |

## §3 Human-in-the-loop & governance

| Blueprint feature | Status | Where / why |
|---|---|---|
| Attribution workspace (raw AI output vs attorney edit, immutable trail) | Neutral equivalent | Model-generated narrative fields are labeled inline `[model-generated]`; everything else is deterministic template or gate-verified quotation. There is no attorney-editing surface in a static demo, so there is no edit-diff pane; the per-draft dossier (below) is the audit trail that exists honestly. |
| Model & system dossier export | Added (this pass) | Each draft ships a provenance dossier: model tag, decoding parameters (temperature 0, pinned seed, context/prediction limits), SHA-256 of the system prompt, of the user prompts, and of the source input text. Reproducibility is checkable end-to-end from the committed snapshots. |
| Form 450 / RBAC conflict-of-interest lockout | Excluded (non-goals + restricted data) | The project is single-user, unauthenticated, and stores no user data (CLAUDE.md non-goals); OGE Form 450 databases are confidential financial-disclosure PII — squarely on the NO-RESTRICTED-DATA exclusion list. |

## §4 System foundation

| Blueprint feature | Status | Where / why |
|---|---|---|
| Air-gapped local open-weights model | Realized | qwen3:8b via Ollama on the local machine, temperature 0, pinned tag; `local`-only mode is the air-gap posture. The blueprint's fine-tuned Llama-3-70B is excluded: fine-tuning is a stated non-goal, and a 70B model does not fit the 16 GB target machine. |
| pgvector + sentence-transformer semantic search | Excluded (stack invariant) | Postgres was dropped from the stack (card-backed hosting); semantic search would also require live compute. The lexical static index above is the zero-cost equivalent. |
| Memgraph real-time graph analytics | Excluded (zero-infra) | See Modality C. |
| LangChain / LlamaIndex unified agentic dashboard | Excluded (deliberate stack decision) | The pipeline is plain typed Python — easier to audit than an orchestration framework (docs/STACK.md). The single-page static UI already unifies every capability in one portal. |

## Summary

Of the blueprint's substantive features: the ingestion, delegation-tracing, drafting-engine,
and air-gapped-model cores were already realized; this pass added lexical search, the
hierarchy browser, the cross-reference view, the three amendatory verb forms, the APA
procedural checklist, and the per-draft provenance dossier. Everything excluded is excluded
by a named, committed invariant — chiefly the §5 neutrality regime (no vulnerability
scoring, no outcome prediction, no deregulatory target lists), the zero-cost/static-export
architecture, and the data-source allow-list — not by omission.
