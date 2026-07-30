"""The corpus scope: which regulations RegLens-31 covers, and the rule that selects them.

Single source of truth for scope. ``reglens.authority.run`` and the ingest CLI
both read these constants, so the covered parts cannot drift between the
pipeline stages and the documents that were actually snapshotted.

The inclusion rule for Federal Register documents is executable rather than
editorial: :func:`reglens.ingest.federal_register.corpus_document_numbers`
returns every final rule the Federal Register's CFR index attributes to any part
in :data:`CFR_PARTS`. Re-running it reproduces the document set.

Known limitation: the FR CFR index only tags documents whose metadata carries a
CFR reference, so some pre-1994 rules are not reachable by this criterion. The
corpus is complete with respect to the stated rule, not with respect to every
rule that has ever touched these parts. See docs/DATA_SOURCES.md.
"""

CFR_TITLE = 31

CFR_PARTS: tuple[int, ...] = (50, 223, 285, 356, 501)
"""Five Title 31 parts spanning three chapters, chosen for drafting-style variety.

Part 50 is the Terrorism Risk Insurance Program (Chapter I, Departmental
Offices); 223 (surety companies), 285 (debt collection) and 356 (marketable
Treasury securities) are Bureau of the Fiscal Service parts in Chapter II; 501
is the OFAC Reporting, Procedures and Penalties Regulations in Chapter V.

Part 501 is admissible under the EXTEND-OGC01 neutrality rules because it is
procedural — reporting, recordkeeping, licensing and penalty procedure — not a
substantive designation program. RegLens-31 makes no designation or screening
determination; see the non-goals in CLAUDE.md section 1.
"""
