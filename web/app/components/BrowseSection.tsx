"use client";

import { useEffect, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import {
  encodePathSegments,
  formatPartHeading,
} from "./search-utils";
import { ExpandableGroup } from "./ui/ExpandableGroup";
import {
  computeHighlightSegments,
  HighlightedText,
} from "./ui/HighlightedText";
import { useLazyJson } from "./ui/useLazyJson";
import { useLazyText } from "./ui/useLazyText";

interface SectionSpan {
  designation: string;
  heading: string;
  start: number;
  end: number;
}

interface SectionsPart {
  part: number;
  heading: string;
  text_path: string;
  sections: SectionSpan[];
}

interface SectionsData {
  title: number;
  parts: SectionsPart[];
}

interface SelectedSection {
  part: SectionsPart;
  section: SectionSpan;
}

export const BROWSE_INTRO =
  "Hierarchical navigation over the five ingested parts of 31 CFR (as of the pinned snapshot date), from part to section. Selecting a section opens the part text at that location. Paragraph-level drill-down is not built.";
const CONTEXT_CHARACTER_COUNT = 500;

interface BrowseSectionProps {
  active: boolean;
  standalone?: boolean;
}

function isSelected(
  selected: SelectedSection | null,
  part: SectionsPart,
  section: SectionSpan,
): boolean {
  return (
    selected?.part.part === part.part &&
    selected.section.start === section.start &&
    selected.section.end === section.end
  );
}

export function BrowseSection({
  active,
  standalone = false,
}: BrowseSectionProps) {
  const { state: sectionsState, load: loadSections } =
    useLazyJson<SectionsData>("/data/sections.json", {
      requestErrorPrefix: "The section index request returned status ",
      fallbackErrorMessage:
        "The Title 31 section index could not be loaded.",
    });
  const { state: partTextState, load: loadPartText } =
    useLazyText<number>({
      requestErrorPrefix: "The part-text request returned status ",
      fallbackErrorMessage:
        "The selected CFR part text could not be loaded.",
    });
  const [expandedParts, setExpandedParts] = useState<Set<number>>(
    () => new Set(),
  );
  const [selectedSection, setSelectedSection] =
    useState<SelectedSection | null>(null);

  useEffect(() => {
    if (active) {
      void loadSections();
    }
  }, [active, loadSections]);

  function togglePart(part: number) {
    setExpandedParts((current) => {
      const next = new Set(current);

      if (next.has(part)) {
        next.delete(part);
      } else {
        next.add(part);
      }

      return next;
    });
  }

  function selectSection(part: SectionsPart, section: SectionSpan) {
    setSelectedSection({ part, section });
    void loadPartText(
      part.part,
      `/data/${encodePathSegments(part.text_path)}`,
    );
  }

  const TitleHeading: "h2" | "h4" = standalone ? "h2" : "h4";

  return (
    <section
      className="eval-section browse-section"
      aria-labelledby={standalone ? undefined : "browse-heading"}
      aria-label={standalone ? "Browse Title 31 (ingested parts)" : undefined}
    >
      {standalone ? null : (
        <h3 id="browse-heading">Browse Title 31 (ingested parts)</h3>
      )}
      <p>{BROWSE_INTRO}</p>

      <div id="browse-section-panel">
        {sectionsState.status === "loading" ? (
          <p role="status">Loading the Title 31 section index…</p>
        ) : null}

        {sectionsState.status === "error" ? (
          <div className="neutral-notice" role="alert">
            <p>
              <strong>Title 31 section index unavailable.</strong>{" "}
              {sectionsState.message}
            </p>
          </div>
        ) : null}

        {sectionsState.status === "ready" ? (
          <>
            <TitleHeading>
              Title 31 — Money and Finance: Treasury
            </TitleHeading>
            <div className="document-groups">
              {sectionsState.data.parts.map((part) => {
                const partIsExpanded = expandedParts.has(part.part);
                const sectionListId = `browse-part-${part.part}-sections`;
                const sectionPanelId = `browse-part-${part.part}-section-panel`;
                const selectedForPart =
                  selectedSection?.part.part === part.part
                    ? selectedSection
                    : null;
                const section = selectedForPart?.section ?? null;
                const textIsCurrent =
                  partTextState.status !== "idle" &&
                  partTextState.key === part.part;
                const highlightResult =
                  section &&
                  textIsCurrent &&
                  partTextState.status === "ready"
                    ? computeHighlightSegments(
                        partTextState.text,
                        section.start,
                        section.end,
                        CONTEXT_CHARACTER_COUNT,
                      )
                    : null;

                return (
                  <ExpandableGroup
                    id={`browse-part-${part.part}`}
                    label={`31 CFR Part ${part.part} — ${formatPartHeading(part.part, part.heading)}`}
                    expanded={partIsExpanded}
                    onToggle={() => togglePart(part.part)}
                    containerId={null}
                    className="document-group"
                    ariaLabelledby={null}
                    panelId={sectionListId}
                    panelClassName={null}
                    renderToggle={({
                      expanded,
                      label,
                      onToggle,
                      panelId,
                    }) => (
                      <Button
                        type="button"
                        outline
                        className="width-full text-left browse-part-button"
                        aria-expanded={expanded}
                        aria-controls={panelId}
                        onClick={onToggle}
                      >
                        {label}
                      </Button>
                    )}
                    key={part.part}
                  >
                    <ul
                      className="claim-list browse-section-list"
                      aria-label={`Sections in 31 CFR Part ${part.part}`}
                    >
                      {part.sections.map((section) => (
                        <li
                          key={`${section.designation}:${section.start}`}
                        >
                          <Button
                            type="button"
                            base
                            outline
                            className="width-full text-left"
                            aria-current={
                              isSelected(selectedSection, part, section)
                                ? "true"
                                : undefined
                            }
                            onClick={() => selectSection(part, section)}
                          >
                            {section.designation} {section.heading}
                          </Button>
                        </li>
                      ))}
                    </ul>

                    <div id={sectionPanelId}>
                      {selectedForPart &&
                      textIsCurrent &&
                      partTextState.status === "loading" ? (
                        <p role="status">
                          Loading 31 CFR Part {part.part} text…
                        </p>
                      ) : null}

                      {selectedForPart &&
                      textIsCurrent &&
                      partTextState.status === "error" ? (
                        <div className="neutral-notice" role="alert">
                          <p>
                            <strong>CFR part text unavailable.</strong>{" "}
                            {partTextState.message}
                          </p>
                        </div>
                      ) : null}

                      {section &&
                      textIsCurrent &&
                      partTextState.status === "ready" &&
                      highlightResult?.status === "ready" ? (
                        <>
                          <p className="browse-context-line">
                            {`Showing ${section.designation} within 31 CFR Part ${part.part}.`}
                          </p>
                          <HighlightedText
                            text={partTextState.text}
                            start={section.start}
                            end={section.end}
                            selectionKey={`${part.part}:${section.start}:${section.end}`}
                            regionLabel={`${section.designation} within 31 CFR Part ${part.part}`}
                            highlightStatus={`Showing ${section.designation} within 31 CFR Part ${part.part}.`}
                            noSpanMessage="The recorded section span falls outside the served CFR part text."
                            boundsMessage="The recorded section span falls outside the served CFR part text."
                            contextChars={CONTEXT_CHARACTER_COUNT}
                            scroll="nearest"
                            scrollBehavior="auto"
                            retryWhenVisible={false}
                            as="pre"
                            showStatus={false}
                          />
                        </>
                      ) : null}

                      {section &&
                      textIsCurrent &&
                      partTextState.status === "ready" &&
                      highlightResult !== null &&
                      highlightResult.status !== "ready" ? (
                        <div className="neutral-notice" role="alert">
                          <p>
                            The recorded section span falls outside the
                            served CFR part text.
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </ExpandableGroup>
                );
              })}
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}
