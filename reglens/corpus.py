"""The corpus scope: which regulations RegLens-31 covers, and the rule that selects them.

Single source of truth for scope. ``reglens.authority.run`` and the ingest CLI
both read these constants, so the covered parts cannot drift between the
pipeline stages and the documents that were actually snapshotted.

Two rules live here, and both are executable rather than editorial:

* **What is in scope** — :func:`reglens.ingest.federal_register.corpus_document_numbers`
  returns every final rule the Federal Register's CFR index attributes to any
  part in :data:`CFR_PARTS`. Re-running it reproduces the document set.
* **What extraction covers** — :func:`in_extraction_sample` selects the subset
  for local-model extraction. The rule is independent of execution order.

Known limitation: the FR CFR index only tags documents whose metadata carries a
CFR reference, so some pre-1994 rules are not reachable by this criterion. The
corpus is complete with respect to the stated rule, not with respect to every
rule that has ever touched these parts. See docs/DATA_SOURCES.md.
"""

import re
from typing import Final

CFR_TITLE = 31

CFR_PARTS: tuple[int, ...] = (50, 223, 285, 356, 501)
"""Five Title 31 parts spanning three chapters, chosen for drafting-style variety.

Part 50 is the Terrorism Risk Insurance Program (Chapter I, Departmental
Offices); 223 (surety companies), 285 (debt collection) and 356 (marketable
Treasury securities) are Bureau of the Fiscal Service parts in Chapter II; 501
is the OFAC Reporting, Procedures and Penalties Regulations in Chapter V.

Part 501 is admissible under the neutrality rules in
docs/OGC01-ALIGNMENT.md because it is procedural — reporting, recordkeeping,
licensing and penalty procedure — not a substantive designation program.
RegLens-31 makes no designation or screening determination; see the non-goals
in CLAUDE.md section 1.
"""


def part_document_number(part: int) -> str:
    """The document number a snapshotted eCFR part text carries, e.g. ``31-CFR-223``.

    This helper provides the canonical identifier used by extraction-scope and
    character-cap policies.
    """
    return f"{CFR_TITLE}-CFR-{part}"


PART_DOCUMENT_NUMBERS: frozenset[str] = frozenset(part_document_number(p) for p in CFR_PARTS)
"""Document numbers of the five in-scope regulation texts (not Federal Register rules)."""


def document_char_cap(document_number: str, default_cap: int) -> int | None:
    """The extraction character cap for one document; ``None`` means uncapped.

    The rule, applied to the corpus rather than to any evaluation set: **the five
    in-scope CFR part texts — the regulations themselves — are extracted in
    full; Federal Register documents are capped at ``default_cap``.** The parts
    are the standing law the tool is about and are bounded in size (the largest
    is ~201k characters), so truncating them would leave the primary subject
    matter partly unread. Federal Register rules are a long tail — one exceeds
    1.3M characters — and stay capped for tractability, with the shortfall
    recorded per document as ``total_chars``/``extracted_chars`` and disclosed.

    Failure mode: none. An unknown document number takes the default cap, so a
    document can never accidentally become uncapped.
    """
    return None if document_number in PART_DOCUMENT_NUMBERS else default_cap


EXTRACTION_YEAR: Final = 2026
"""Publication year whose Federal Register documents extraction covers."""

_PUBLICATION_DATE = re.compile(r"^(\d{4})-\d{2}-\d{2}$")


def in_extraction_sample(document_number: str, publication_date: str) -> bool:
    """Whether extraction covers this in-scope document — the sampling rule, in code.

    The rule: **the five in-scope CFR part texts, plus every in-scope Federal
    Register document published in :data:`EXTRACTION_YEAR`.** The parts are the
    standing law the tool is about; the year bounds the rulemaking that amended
    it most recently.

    Why a sample at all: inference runs entirely on one laptop (CLAUDE.md
    section 1), so extracting every in-scope document is hours of local compute
    that would have to be repeated on every model or prompt change. Every
    in-scope document is still ingested, content-addressed and committed —
    widening the sample is a parameter change, not a data-collection exercise.
    The executable boundary is checkable, reproducible, and independent of
    which documents happen to run first.

    Failure mode: fail-closed. A Federal Register document whose publication
    date is missing or not an ISO date is excluded, because a document that
    cannot be placed in a year cannot be shown to satisfy the rule.
    """
    if document_number in PART_DOCUMENT_NUMBERS:
        return True
    matched = _PUBLICATION_DATE.match(publication_date)
    return matched is not None and matched.group(1) == str(EXTRACTION_YEAR)
