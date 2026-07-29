"""Typed section structure derived from flattened CFR part text.

Inputs are a caller-supplied CFR part number, part heading, source path, and
the exact flattened text snapshot. Outputs are pydantic models containing
section designations, headings, and offsets into that unchanged text. The
splitter raises ``ValueError`` when it cannot find a plausible section heading
for the requested part.
"""

import re
from collections.abc import Sequence

from pydantic import BaseModel, Field

type _SectionCandidate = tuple[int, int, int, str, str]

_DOTTED_INITIALISM = re.compile(r"(?<![A-Za-z])(?:[A-Z]\.){2,}")


class SectionSpan(BaseModel):
    """One CFR section's label and half-open span in a flattened part.

    Inputs are the exact designation and heading text plus ``start`` and
    ``end`` character offsets. The output is a typed pydantic record;
    pydantic raises ``ValidationError`` for invalid field types or negative
    offsets.
    """

    designation: str
    heading: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class PartStructure(BaseModel):
    """The ordered section structure for one CFR part text snapshot.

    Inputs identify the part, its caller-supplied heading and text path, and
    its section spans. The output is a typed pydantic record; pydantic raises
    ``ValidationError`` when a field has an invalid type or nested value.
    """

    part: int
    heading: str
    text_path: str
    sections: list[SectionSpan]
    # Transparency counter: heading-shaped candidates the splitter did NOT
    # accept (false-positive filtering). A nonzero value on a corpus refresh
    # is the signal to re-inspect coverage rather than trust silence.
    rejected_candidates: int = Field(default=0, ge=0)


class SectionsExport(BaseModel):
    """A title-level collection of structured CFR parts.

    Inputs are the CFR title number and ordered part structures. The output is
    a typed pydantic export record; pydantic raises ``ValidationError`` when a
    field or nested model is invalid.
    """

    title: int
    parts: list[PartStructure]


def build_sections_export(*, title: int, parts: Sequence[PartStructure]) -> SectionsExport:
    """Build an owned, order-preserving title-level sections export.

    Args:
        title: CFR title number to store on the export.
        parts: Ordered part structures to copy into the export.

    Returns:
        A ``SectionsExport`` containing a new list in the input sequence's
        original order.

    Raises:
        pydantic.ValidationError: If ``title`` or any part fails pydantic
            validation; the validation failure propagates unchanged.
    """
    return SectionsExport(title=title, parts=list(parts))


def _heading_from_line_tail(line_tail: str) -> str | None:
    """Extract a plausible section heading from text after a designation.

    Args:
        line_tail: Exact text from after the designation through the line end.

    Returns:
        The heading prefix including its terminal period or question mark, or
        ``[Reserved]`` for a reserved section. Periods inside dotted uppercase
        initialisms such as ``U.S.`` and ``U.S.C.`` are skipped.

    Failure mode:
        Returns ``None`` when the line does not begin with an uppercase heading
        or does not contain a plausible heading terminator.
    """
    if line_tail.rstrip(" \t") == "[Reserved]":
        return "[Reserved]"
    if not line_tail or not line_tail[0].isupper():
        return None

    initialism_spans = [
        (match.start(), match.end()) for match in _DOTTED_INITIALISM.finditer(line_tail)
    ]
    for index, character in enumerate(line_tail):
        if character not in ".?":
            continue
        if character == "." and any(start <= index < end for start, end in initialism_spans):
            continue
        if index + 1 == len(line_tail) or line_tail[index + 1] in " \t":
            return line_tail[: index + 1]
    return None


def _select_increasing_candidates(
    candidates: Sequence[_SectionCandidate],
) -> list[_SectionCandidate]:
    """Select the most plausible ordered section sequence.

    Args:
        candidates: Text-ordered tuples of start offset, first section number,
            terminal range number, exact designation, and heading.

    Returns:
        The longest sequence whose next first number is greater than the prior
        terminal number. Equal-length sequences prefer the smaller terminal
        number; remaining ties prefer later candidate occurrences.

    Failure mode:
        Returns an empty list when ``candidates`` is empty; it does not raise.
    """
    if not candidates:
        return []

    best_paths: list[tuple[int, ...]] = []
    for index, candidate in enumerate(candidates):
        best_path = (index,)
        for prior_index in range(index):
            if candidates[prior_index][2] >= candidate[1]:
                continue
            contender = (*best_paths[prior_index], index)
            if (len(contender), contender) > (len(best_path), best_path):
                best_path = contender
        best_paths.append(best_path)

    selected_indices = max(
        best_paths,
        key=lambda path: (len(path), -candidates[path[-1]][2], path),
    )
    return [candidates[index] for index in selected_indices]


def split_part_text(*, part: int, heading: str, text_path: str, text: str) -> PartStructure:
    """Split one flattened CFR part into plausible, ordered section spans.

    Args:
        part: CFR part number whose section designations may be accepted.
        heading: Part heading to preserve verbatim in the result.
        text_path: Caller-supplied path identifying the text snapshot.
        text: Exact flattened text whose character offsets must be retained.

    Returns:
        A ``PartStructure`` whose spans begin at accepted designations and end
        at the next accepted designation or at ``len(text)``.

    Raises:
        ValueError: If no plausible section headings for ``part`` are found,
            or if an accepted designation does not occur at its recorded
            offset.
    """
    part_text = re.escape(str(part))
    section_pattern = re.compile(
        rf"^(?P<designation>§(?P<plural>§)?[ \t]+"
        rf"{part_text}\.(?P<first>\d+)"
        rf"(?P<range>-(?:{part_text}\.)?(?P<last>\d+))?)"
        rf"[ \t]+(?P<line_tail>[^\r\n]*)",
        flags=re.MULTILINE,
    )

    candidates: list[_SectionCandidate] = []
    for match in section_pattern.finditer(text):
        is_plural = match.group("plural") is not None
        range_end_text = match.group("last")
        is_range = range_end_text is not None
        section_number = int(match.group("first"))
        range_end = int(range_end_text) if range_end_text is not None else section_number
        section_heading = _heading_from_line_tail(match.group("line_tail"))

        if is_plural != is_range:
            continue
        if section_heading is None:
            continue
        if is_range and (section_heading != "[Reserved]" or range_end < section_number):
            continue

        candidates.append(
            (
                match.start(),
                section_number,
                range_end,
                match.group("designation"),
                section_heading,
            )
        )

    accepted = _select_increasing_candidates(candidates)
    if not accepted:
        raise ValueError(f"No plausible section headings found for part {part}")

    # Offsets are correct by construction here (each start is a finditer match
    # position); the meaningful re-validation happens in export, which re-reads
    # the published text from disk and re-checks every span against it.
    sections: list[SectionSpan] = []
    for index, (start, _, _, designation, section_heading) in enumerate(accepted):
        end = accepted[index + 1][0] if index + 1 < len(accepted) else len(text)
        sections.append(
            SectionSpan(
                designation=designation,
                heading=section_heading,
                start=start,
                end=end,
            )
        )

    return PartStructure(
        part=part,
        heading=heading,
        text_path=text_path,
        sections=sections,
        rejected_candidates=len(candidates) - len(accepted),
    )
