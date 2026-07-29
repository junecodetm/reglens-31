"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import { buildAuthorityCrossReferences } from "./crossref-utils";
import type { AuthorityData } from "./reglens-types";

type AuthorityState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: AuthorityData }
  | { status: "error"; message: string };

const CROSS_REF_INTRO =
  "Which U.S. Code sections each ingested CFR part cites as rulemaking authority, and which cited sections are shared across parts. Retrieval over the parsed authority citations only — this is not a dependency, impact, or conflict analysis. Citations that did not resolve in the pinned U.S. Code release are listed separately as coverage facts.";

export function CrossRefSection() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [authorityState, setAuthorityState] = useState<AuthorityState>({
    status: "idle",
  });
  const requestStartedRef = useRef(false);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  async function loadAuthorityData() {
    if (requestStartedRef.current) {
      return;
    }

    requestStartedRef.current = true;
    const controller = new AbortController();
    controllerRef.current = controller;
    setAuthorityState({ status: "loading" });

    try {
      const response = await fetch("/data/authority.json", {
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(
          `The authority request returned status ${response.status}.`,
        );
      }

      const data = (await response.json()) as AuthorityData;

      if (!controller.signal.aborted) {
        setAuthorityState({ status: "ready", data });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setAuthorityState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "The authority cross-reference data could not be loaded.",
        });
      }
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }
    }
  }

  function toggleSection() {
    const willExpand = !isExpanded;
    setIsExpanded(willExpand);

    if (willExpand && authorityState.status === "idle") {
      void loadAuthorityData();
    }
  }

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

  return (
    <section
      className="eval-section cross-ref-section"
      aria-labelledby="cross-ref-heading"
    >
      <h2 id="cross-ref-heading">Authority cross-references</h2>
      <p>{CROSS_REF_INTRO}</p>

      <Button
        type="button"
        base
        outline
        aria-expanded={isExpanded}
        aria-controls="cross-ref-section-panel"
        onClick={toggleSection}
      >
        {isExpanded
          ? "Collapse authority cross-references"
          : "Expand authority cross-references"}
      </Button>

      <div id="cross-ref-section-panel" hidden={!isExpanded}>
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
              <h3 id="cross-ref-by-part-heading">By CFR part</h3>

              {sortedParts.map((part) => (
                <section
                  className="cross-ref-group"
                  aria-labelledby={`cross-ref-part-${part.part}-heading`}
                  key={part.part}
                >
                  <h4 id={`cross-ref-part-${part.part}-heading`}>
                    31 CFR Part {part.part}
                  </h4>
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
              <h3 id="cross-ref-by-usc-heading">By U.S. Code section</h3>
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
