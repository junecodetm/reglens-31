import type { AuthorityData } from "./reglens-types";

export interface AuthorityCrossReference {
  uscTitle: number;
  uscSection: string;
  parts: number[];
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
