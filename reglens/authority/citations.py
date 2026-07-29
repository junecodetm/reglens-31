"""Authority-citation extraction and parsing.

Inputs: a part's eCFR XML (``<AUTH><PSPACE>``) and its flattened text
snapshot. Outputs: the verbatim authority line located in the text (with
gate-verified offsets) and a typed list of :class:`AuthorityCitation`.
Failure mode: a missing/empty AUTH element raises ``LookupError``; a segment
the grammar cannot type is preserved as an unclassified public-law citation
only when it names a Public Law, otherwise parsing raises — nothing is
silently dropped or guessed (fail-closed).

Design note: a small hand-rolled grammar over the observed authority-line
forms (semicolon-separated segments; per-title section lists; ranges;
"et seq."; parenthetical "(NN U.S.C. NNNN note)"; Pub. L.; E.O.). The
``eyecite`` library was considered and rejected: it targets case-law
citations and would add a dependency for a narrower, more predictable task.
"""

import re
from xml.etree import ElementTree

from reglens.authority.records import AuthorityCitation, CitationKind
from reglens.provenance import verify_span

_USC_LIST = re.compile(r"^(\d+)\s+U\.S\.C\.\s+(.+)$")
_NOTE_PAREN = re.compile(r"\((\d+)\s+U\.S\.C\.\s+([0-9]+[A-Za-z0-9-]*)\s+note\)")
_SECTION_TOKEN = re.compile(r"^([0-9]+[A-Za-z]*)(\([A-Za-z0-9]+\))?$")
_RANGE_TOKEN = re.compile(r"^([0-9]+)-([0-9]+)$")

# Expanding a range beyond this bound would indicate a mis-parse, not a real
# authority citation; fail closed rather than fabricate hundreds of cites.
_MAX_RANGE_SPAN = 60


class AuthorityParseError(ValueError):
    """Raised when an authority segment cannot be typed by the grammar."""


def extract_authority_text(xml_bytes: bytes) -> str:
    """Verbatim authority line from ``<AUTH>`` (tag boundaries flattened).

    Failure mode: raises ``LookupError`` when no AUTH element exists —
    a part without a parseable authority citation must surface, not vanish.
    """
    root = ElementTree.fromstring(xml_bytes)
    auth = root.find(".//AUTH")
    if auth is None:
        raise LookupError("part XML has no AUTH element")
    text = " ".join(fragment.strip() for fragment in auth.itertext() if fragment.strip())
    if not text:
        raise LookupError("part XML AUTH element is empty")
    return text


def extract_part_heading(xml_bytes: bytes) -> str:
    """The part's HEAD line (e.g. "PART 501—REPORTING …").

    Failure mode: raises ``LookupError`` when absent — draft skeletons must
    carry the real part heading or none at all, never an invented one.
    """
    root = ElementTree.fromstring(xml_bytes)
    for div in root.iter():
        if div.get("TYPE") == "PART":
            head = div.find("HEAD")
            if head is not None:
                text = " ".join(f.strip() for f in head.itertext() if f.strip())
                if text:
                    return text
    raise LookupError("part XML has no PART HEAD element")


def locate_authority_span(part_text: str, authority_text: str) -> tuple[int, int]:
    """Gate-verified offsets of the authority line inside the part text.

    Reuses the provenance gate so the UI highlight can never point at text
    that is not verbatim present. Failure mode: raises ``LookupError`` when
    verification fails (fail-closed — no unverified offsets leave here).
    """
    result = verify_span(part_text, authority_text)
    if not result.accepted or result.start is None or result.end is None:
        raise LookupError(f"authority text failed the provenance gate: {result.reason}")
    return result.start, result.end


def _expand_section_list(title: int, body: str) -> list[AuthorityCitation]:
    """Expand one ``NN U.S.C. <tokens>`` segment into typed citations."""
    citations: list[AuthorityCitation] = []
    # "3102, et seq." — the flag binds to the previous token after the comma.
    body = re.sub(r",\s*et\s+seq\.?", " et-seq-marker", body)
    tokens = [token.strip().rstrip(".") for token in body.split(",")]
    for token in tokens:
        if not token:
            continue
        et_seq = token.endswith("et-seq-marker")
        token = token.replace("et-seq-marker", "").strip()
        range_match = _RANGE_TOKEN.match(token)
        if range_match:
            low, high = int(range_match.group(1)), int(range_match.group(2))
            if high <= low or high - low > _MAX_RANGE_SPAN:
                # Fail-closed: an implausible range is a parse error, not a
                # license to fabricate citations.
                raise AuthorityParseError(f"implausible section range: {title} U.S.C. {token}")
            citations.extend(
                AuthorityCitation(
                    raw=f"{title} U.S.C. {number}",
                    kind=CitationKind.usc_section,
                    usc_title=title,
                    usc_section=str(number),
                    from_range=f"{title} U.S.C. {token}",
                )
                for number in range(low, high + 1)
            )
            continue
        token_match = _SECTION_TOKEN.match(token)
        if token_match is None:
            raise AuthorityParseError(f"unrecognized section token: {title} U.S.C. {token!r}")
        section, subsection = token_match.group(1), token_match.group(2)
        citations.append(
            AuthorityCitation(
                raw=f"{title} U.S.C. {token}" + (" et seq." if et_seq else ""),
                kind=CitationKind.usc_section,
                usc_title=title,
                usc_section=section,
                subsection=subsection,
                et_seq=et_seq,
            )
        )
    return citations


def parse_authority(authority_text: str) -> list[AuthorityCitation]:
    """Parse an authority line into typed citations.

    Segments are split on ";" after stripping the "Authority:" prefix. Typing
    precedence within a segment: E.O. → Pub. L. (with a parenthetical
    "(NN U.S.C. NNNN note)" becoming ``usc_note``) → "NN U.S.C." section
    list. Failure mode: :class:`AuthorityParseError` on any segment the
    grammar cannot type — never silently skipped.
    """
    text = re.sub(r"^\s*Authority:\s*", "", authority_text).strip().rstrip(".")
    citations: list[AuthorityCitation] = []
    for raw_segment in text.split(";"):
        segment = raw_segment.strip()
        if not segment:
            continue
        if re.search(r"\bE\.O\.\s*\d+", segment):
            citations.append(AuthorityCitation(raw=segment, kind=CitationKind.executive_order))
            continue
        if "Pub. L." in segment:
            note = _NOTE_PAREN.search(segment)
            if note:
                citations.append(
                    AuthorityCitation(
                        raw=segment,
                        kind=CitationKind.usc_note,
                        usc_title=int(note.group(1)),
                        usc_section=note.group(2),
                    )
                )
            else:
                citations.append(AuthorityCitation(raw=segment, kind=CitationKind.public_law))
            continue
        usc = _USC_LIST.match(segment)
        if usc:
            citations.extend(_expand_section_list(int(usc.group(1)), usc.group(2)))
            continue
        raise AuthorityParseError(f"cannot type authority segment: {segment!r}")
    return citations
