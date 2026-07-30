import type { AuthorityData } from "./reglens-types";

type AuthorityPart = AuthorityData["parts"][number];
type ResolvedAuthoritySection = AuthorityPart["resolved"][number];

function shouldAutoShowAuthoritySection(
  section: ResolvedAuthoritySection,
): boolean {
  return (
    section.classification === "mandatory" ||
    section.classification === "discretionary" ||
    section.verb_quote !== null
  );
}

export interface AuthorityCrossReference {
  uscTitle: number;
  uscSection: string;
  parts: number[];
}

export interface AuthoritySectionGroup {
  range: string | null;
  sections: ResolvedAuthoritySection[];
  visibleSections: ResolvedAuthoritySection[];
  silentSections: ResolvedAuthoritySection[];
}

export function groupAuthoritySections(
  part: AuthorityPart,
): AuthoritySectionGroup[] {
  const sectionsByRange = new Map<
    string | null,
    ResolvedAuthoritySection[]
  >();

  for (const section of part.resolved) {
    const citation = part.citations.find(
      (candidate) =>
        candidate.kind === "usc-section" &&
        candidate.usc_title === section.usc_title &&
        candidate.usc_section === section.usc_section,
    );
    const range = citation?.from_range ?? null;
    const sections = sectionsByRange.get(range);

    if (sections) {
      sections.push(section);
    } else {
      sectionsByRange.set(range, [section]);
    }
  }

  return [...sectionsByRange.entries()].map(([range, sections]) => {
    if (range === null) {
      return {
        range,
        sections,
        visibleSections: sections,
        silentSections: [],
      };
    }

    const visibleSections = sections.filter(
      shouldAutoShowAuthoritySection,
    );
    const silentSections = sections.filter(
      (section) => !shouldAutoShowAuthoritySection(section),
    );

    return {
      range,
      sections,
      visibleSections,
      silentSections,
    };
  });
}

export function buildAuthorityCrossReferences(
  data: AuthorityData,
): AuthorityCrossReference[] {
  const authorities = new Map<
    string,
    { uscTitle: number; uscSection: string; parts: Set<number> }
  >();

  for (const part of data.parts) {
    for (const section of part.resolved) {
      const key = `${section.usc_title}:${section.usc_section}`;
      const existing = authorities.get(key);

      if (existing) {
        existing.parts.add(part.part);
      } else {
        authorities.set(key, {
          uscTitle: section.usc_title,
          uscSection: section.usc_section,
          parts: new Set([part.part]),
        });
      }
    }
  }

  return [...authorities.values()]
    .map(({ uscTitle, uscSection, parts }) => ({
      uscTitle,
      uscSection,
      parts: [...parts].sort((left, right) => left - right),
    }))
    .sort((left, right) => {
      const sharedOrder =
        Number(right.parts.length > 1) - Number(left.parts.length > 1);

      return (
        sharedOrder ||
        left.uscTitle - right.uscTitle ||
        left.uscSection.localeCompare(right.uscSection, "en-US", {
          numeric: true,
        })
      );
    });
}
