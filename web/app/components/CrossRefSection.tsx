"use client";

import { useEffect } from "react";

import { buildAuthorityCrossReferences } from "./crossref-utils";
import type { AuthorityData } from "./reglens-types";
import { useLazyJson } from "./ui/useLazyJson";

export const CROSS_REF_INTRO =
  "Which U.S. Code sections each ingested CFR part cites as rulemaking authority, and which cited sections are shared across parts. Retrieval over the parsed authority citations only — this is not a dependency, impact, or conflict analysis. Citations that did not resolve in the pinned U.S. Code release are listed separately as coverage facts.";

interface CrossRefSectionProps {
  active: boolean;
  standalone?: boolean;
}

export function CrossRefSection({
  active,
  standalone = false,
}: CrossRefSectionProps) {
  const { state: authorityState, load: loadAuthorityData } =
    useLazyJson<AuthorityData>("/data/authority.json", {
      requestErrorPrefix: "The authority request returned status ",
      fallbackErrorMessage:
        "The authority cross-reference data could not be loaded.",
    });

  useEffect(() => {
    if (active) {
      void loadAuthorityData();
    }
  }, [active, loadAuthorityData]);

  const sortedParts =
    authorityState.status === "ready"
      ? [...authorityState.data.parts].sort(
          (left, right) => left.part - right.part,
        )
      : [];
  const crossReferences =
    authorityState.status === "ready"
      ? buildAuthorityCrossReferences(authorityState.data)
      : [];
  const ViewHeading: "h2" | "h4" = standalone ? "h2" : "h4";
  const GroupHeading: "h3" | "h5" = standalone ? "h3" : "h5";

  return (
    <section
      className="eval-section cross-ref-section"
      aria-labelledby={standalone ? undefined : "cross-ref-heading"}
      aria-label={standalone ? "Authority cross-references" : undefined}
    >
      {standalone ? null : (
        <h3 id="cross-ref-heading">Authority cross-references</h3>
      )}
      <p>{CROSS_REF_INTRO}</p>

      <div id="cross-ref-section-panel">
        {authorityState.status === "loading" ? (
          <p role="status">Loading authority cross-references…</p>
        ) : null}

        {authorityState.status === "error" ? (
          <div className="neutral-notice" role="alert">
            <p>
              <strong>Authority cross-references unavailable.</strong>{" "}
              {authorityState.message}
            </p>
          </div>
        ) : null}

        {authorityState.status === "ready" ? (
          <div className="cross-ref-views">
            <section aria-labelledby="cross-ref-by-part-heading">
              <ViewHeading id="cross-ref-by-part-heading">
                By CFR part
              </ViewHeading>

              {sortedParts.map((part) => (
                <section
                  className="cross-ref-group"
                  aria-labelledby={`cross-ref-part-${part.part}-heading`}
                  key={part.part}
                >
                  <GroupHeading id={`cross-ref-part-${part.part}-heading`}>
                    31 CFR Part {part.part}
                  </GroupHeading>
                  <ul className="usa-list">
                    {part.resolved.map((section) => (
                      <li key={section.identifier}>
                        {section.usc_title} U.S.C. § {section.usc_section}
                        {section.heading ? ` — ${section.heading}` : ""}
                      </li>
                    ))}
                  </ul>
                  {part.unresolved.length > 0 ? (
                    <p>
                      Unresolved citations: {part.unresolved.length} (coverage
                      fact)
                    </p>
                  ) : null}
                </section>
              ))}
            </section>

            <section aria-labelledby="cross-ref-by-usc-heading">
              <ViewHeading id="cross-ref-by-usc-heading">
                By U.S. Code section
              </ViewHeading>
              <p>
                Shared authorities (cited by more than one part) appear first.
              </p>
              <ul className="usa-list">
                {crossReferences.map((reference) => (
                  <li
                    key={`${reference.uscTitle}:${reference.uscSection}`}
                  >
                    <p>
                      <strong>
                        {reference.uscTitle} U.S.C. § {reference.uscSection}
                      </strong>
                    </p>
                    <p>
                      Cited as authority by:{" "}
                      {reference.parts
                        .map((part) => `31 CFR Part ${part}`)
                        .join(", ")}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        ) : null}
      </div>
    </section>
  );
}
