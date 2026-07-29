"""Tests for splitting flattened CFR part text into section spans."""

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parents[1] / "web" / "public" / "data" / "authority-parts"
EXPECTED_PART_FILES = {
    "31-CFR-50.txt",
    "31-CFR-223.txt",
    "31-CFR-285.txt",
    "31-CFR-356.txt",
    "31-CFR-501.txt",
}


def test_split_part_text_preserves_headings_and_exact_offsets() -> None:
    """Each section spans from its designation through the next section."""
    from reglens.structure import PartStructure, SectionsExport, SectionSpan, split_part_text

    text = (
        "PART 50—TEST PART\n\n"
        "§ 50.1 Purpose. First section body.\n"
        "Still part of the first section.\n"
        "§ 50.2 Who must comply? Second section body."
    )
    first_start = text.index("§ 50.1")
    second_start = text.index("§ 50.2")

    result = split_part_text(
        part=50,
        heading="Test Part",
        text_path="snapshots/31-CFR-50.txt",
        text=text,
    )

    expected = PartStructure(
        part=50,
        heading="Test Part",
        text_path="snapshots/31-CFR-50.txt",
        sections=[
            SectionSpan(
                designation="§ 50.1",
                heading="Purpose.",
                start=first_start,
                end=second_start,
            ),
            SectionSpan(
                designation="§ 50.2",
                heading="Who must comply?",
                start=second_start,
                end=len(text),
            ),
        ],
    )
    assert result == expected
    assert SectionsExport(title=31, parts=[result]).parts == [expected]


def test_build_sections_export_copies_parts_in_input_order() -> None:
    """The export builder owns its ordered list instead of aliasing the input."""
    from reglens.structure import PartStructure, build_sections_export

    first = PartStructure(
        part=223,
        heading="Surety Companies",
        text_path="part-223.txt",
        sections=[],
    )
    second = PartStructure(
        part=50,
        heading="Terrorism Risk Insurance Program",
        text_path="part-50.txt",
        sections=[],
    )
    parts = [first, second]

    result = build_sections_export(title=31, parts=parts)
    parts.reverse()

    assert result.title == 31
    assert result.parts == [first, second]
    assert result.parts is not parts


def test_split_part_text_keeps_dotted_initialisms_inside_headings() -> None:
    """A dotted initialism does not terminate its section heading early."""
    from reglens.structure import split_part_text

    text = "§ 50.1 U.S. persons. Body."

    result = split_part_text(part=50, heading="Test Part", text_path="part-50.txt", text=text)

    assert result.sections[0].heading == "U.S. persons."


def test_split_part_text_rejects_plausible_uppercase_forward_references() -> None:
    """A forward inline reference cannot displace the next real section."""
    from reglens.structure import split_part_text

    text = (
        "§ 50.1 Purpose. See\n"
        "§ 50.99 Reporting. inline reference\n"
        "§ 50.2 Scope. Real second section."
    )
    real_second_start = text.index("§ 50.2")

    result = split_part_text(part=50, heading="Test Part", text_path="part-50.txt", text=text)

    assert [section.designation for section in result.sections] == ["§ 50.1", "§ 50.2"]
    assert result.sections[0].end == real_second_start


def test_split_part_text_rejects_line_broken_cross_references() -> None:
    """Lowercase, duplicate, and backward references do not create sections."""
    from reglens.structure import split_part_text

    text = (
        "§ 50.1 Purpose. See the requirements in\n"
        "§ 50.99 of this part.\n"
        "§ 50.1 Purpose. repeated as an inline reference.\n"
        "§ 49.9 Wrong-part heading. also appears inline.\n"
        "§ 50.2 Scope. This is the next real section."
    )
    second_start = text.index("§ 50.2")

    result = split_part_text(part=50, heading="Test Part", text_path="part-50.txt", text=text)

    assert [section.designation for section in result.sections] == ["§ 50.1", "§ 50.2"]
    assert result.sections[0].end == second_start


def test_split_part_text_supports_plural_reserved_ranges() -> None:
    """A plural reserved range is retained with its exact designation."""
    from reglens.structure import split_part_text

    text = "§ 223.12 Notice. Body.\n§§ 223.13-223.14 [Reserved]\n§ 223.15 Fees. Body."
    range_start = text.index("§§ 223.13")
    next_start = text.index("§ 223.15")

    result = split_part_text(
        part=223,
        heading="Surety Companies",
        text_path="part-223.txt",
        text=text,
    )

    reserved = result.sections[1]
    assert reserved.designation == "§§ 223.13-223.14"
    assert reserved.heading == "[Reserved]"
    assert reserved.start == range_start
    assert reserved.end == next_start


def test_split_part_text_requires_at_least_one_section() -> None:
    """A part-specific ValueError is raised when no section can be found."""
    from reglens.structure import split_part_text

    with pytest.raises(ValueError, match=r"part 50"):
        split_part_text(
            part=50,
            heading="Test Part",
            text_path="part-50.txt",
            text="§ 51.1 Other part. This heading belongs elsewhere.",
        )


@pytest.mark.skipif(not DATA_DIR.is_dir(), reason="authority-part fixture directory is absent")
def test_all_authority_part_snapshots_split_with_valid_offsets() -> None:
    """All checked-in authority snapshots split into contiguous valid spans."""
    from reglens.structure import split_part_text

    paths = sorted(DATA_DIR.glob("*.txt"))
    assert {path.name for path in paths} == EXPECTED_PART_FILES

    for path in paths:
        part = int(path.stem.removeprefix("31-CFR-"))
        text = path.read_text(encoding="utf-8")
        result = split_part_text(
            part=part,
            heading=f"Part {part}",
            text_path=str(path),
            text=text,
        )

        assert result.part == part
        assert result.heading == f"Part {part}"
        assert result.text_path == str(path)
        assert result.sections
        assert result.sections[-1].end == len(text)

        for index, section in enumerate(result.sections):
            assert 0 <= section.start < section.end <= len(text)
            assert text[section.start :].startswith(section.designation)
            if index:
                assert result.sections[index - 1].end == section.start
