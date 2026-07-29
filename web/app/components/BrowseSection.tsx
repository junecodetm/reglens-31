"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import { encodePathSegments } from "./search-utils";

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

interface ContextSegments {
  before: string;
  highlighted: string;
  after: string;
}

type SectionsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: SectionsData }
  | { status: "error"; message: string };

type PartTextState =
  | { status: "idle" }
  | { status: "loading"; key: number }
  | { status: "ready"; key: number; text: string }
  | { status: "error"; key: number; message: string };

const BROWSE_INTRO =
  "Hierarchical navigation over the five ingested parts of 31 CFR (as of the pinned snapshot date), from part to section. Selecting a section opens the part text at that location. Paragraph-level drill-down is not built.";
const CONTEXT_CHARACTER_COUNT = 500;

function getContextSegments(
  text: string,
  section: SectionSpan,
): ContextSegments | null {
  if (
    !Number.isInteger(section.start) ||
    !Number.isInteger(section.end) ||
    section.start < 0 ||
    section.end <= section.start ||
    section.end > text.length
  ) {
    return null;
  }

  return {
    before: text.slice(
      Math.max(0, section.start - CONTEXT_CHARACTER_COUNT),
      section.start,
    ),
    highlighted: text.slice(section.start, section.end),
    after: text.slice(
      section.end,
      Math.min(text.length, section.end + CONTEXT_CHARACTER_COUNT),
    ),
  };
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

export function BrowseSection() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [sectionsState, setSectionsState] = useState<SectionsState>({
    status: "idle",
  });
  const [expandedParts, setExpandedParts] = useState<Set<number>>(
    () => new Set(),
  );
  const [selectedSection, setSelectedSection] =
    useState<SelectedSection | null>(null);
  const [partTextState, setPartTextState] = useState<PartTextState>({
    status: "idle",
  });

  const sectionsRequestedRef = useRef(false);
  const sectionsControllerRef = useRef<AbortController | null>(null);
  const partControllerRef = useRef<AbortController | null>(null);
  const partTextCacheRef = useRef<Map<number, string>>(new Map());
  const markRef = useRef<HTMLElement>(null);

  const selectionKey = selectedSection
    ? `${selectedSection.part.part}:${selectedSection.section.start}:${selectedSection.section.end}`
    : null;

  useEffect(() => {
    return () => {
      sectionsControllerRef.current?.abort();
      partControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (
      selectionKey !== null &&
      partTextState.status === "ready" &&
      markRef.current
    ) {
      markRef.current.scrollIntoView({ block: "nearest" });
    }
  }, [partTextState, selectionKey]);

  async function loadSections() {
    if (sectionsRequestedRef.current) {
      return;
    }

    sectionsRequestedRef.current = true;
    const controller = new AbortController();
    sectionsControllerRef.current = controller;
    setSectionsState({ status: "loading" });

    try {
      const response = await fetch("/data/sections.json", {
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(
          `The section index request returned status ${response.status}.`,
        );
      }

      const data = (await response.json()) as SectionsData;

      if (!controller.signal.aborted) {
        setSectionsState({ status: "ready", data });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setSectionsState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "The Title 31 section index could not be loaded.",
        });
      }
    } finally {
      if (sectionsControllerRef.current === controller) {
        sectionsControllerRef.current = null;
      }
    }
  }

  async function loadPartText(part: SectionsPart) {
    if (
      partTextState.status === "loading" &&
      partTextState.key === part.part
    ) {
      return;
    }

    partControllerRef.current?.abort();
    partControllerRef.current = null;

    const cached = partTextCacheRef.current.get(part.part);

    if (cached !== undefined) {
      setPartTextState({ status: "ready", key: part.part, text: cached });
      return;
    }

    const controller = new AbortController();
    partControllerRef.current = controller;
    setPartTextState({ status: "loading", key: part.part });

    try {
      const response = await fetch(
        `/data/${encodePathSegments(part.text_path)}`,
        { signal: controller.signal },
      );

      if (!response.ok) {
        throw new Error(
          `The part-text request returned status ${response.status}.`,
        );
      }

      const text = await response.text();

      if (!controller.signal.aborted) {
        partTextCacheRef.current.set(part.part, text);
        setPartTextState({ status: "ready", key: part.part, text });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setPartTextState({
          status: "error",
          key: part.part,
          message:
            error instanceof Error
              ? error.message
              : "The selected CFR part text could not be loaded.",
        });
      }
    } finally {
      if (partControllerRef.current === controller) {
        partControllerRef.current = null;
      }
    }
  }

  function toggleSection() {
    const willExpand = !isExpanded;
    setIsExpanded(willExpand);

    if (willExpand && sectionsState.status === "idle") {
      void loadSections();
    }
  }

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
    void loadPartText(part);
  }

  return (
    <section
      className="eval-section browse-section"
      aria-labelledby="browse-heading"
    >
      <h2 id="browse-heading">Browse Title 31 (ingested parts)</h2>
      <p>{BROWSE_INTRO}</p>

      <Button
        type="button"
        base
        outline
        aria-expanded={isExpanded}
        aria-controls="browse-section-panel"
        onClick={toggleSection}
      >
        {isExpanded
          ? "Collapse Title 31 browser"
          : "Expand Title 31 browser"}
      </Button>

      <div id="browse-section-panel" hidden={!isExpanded}>
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
            <h3>Title 31 — Money and Finance: Treasury</h3>
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
                const contextSegments =
                  section &&
                  textIsCurrent &&
                  partTextState.status === "ready"
                    ? getContextSegments(
                        partTextState.text,
                        section,
                      )
                    : null;

                return (
                  <article className="document-group" key={part.part}>
                    <Button
                      type="button"
                      base
                      outline
                      className="width-full text-left"
                      aria-expanded={partIsExpanded}
                      aria-controls={sectionListId}
                      onClick={() => togglePart(part.part)}
                    >
                      31 CFR Part {part.part} — {part.heading}
                    </Button>

                    <div id={sectionListId} hidden={!partIsExpanded}>
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
                              aria-expanded={isSelected(
                                selectedSection,
                                part,
                                section,
                              )}
                              aria-controls={sectionPanelId}
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
                        contextSegments ? (
                          <>
                            <p className="browse-context-line">
                              {`Showing ${section.designation} within 31 CFR Part ${part.part}.`}
                            </p>
                            <pre
                              className="source-document"
                              tabIndex={0}
                              role="region"
                              aria-label={`${section.designation} within 31 CFR Part ${part.part}`}
                            >
                              {contextSegments.before}
                              <mark ref={markRef}>
                                {contextSegments.highlighted}
                              </mark>
                              {contextSegments.after}
                            </pre>
                          </>
                        ) : null}

                        {section &&
                        textIsCurrent &&
                        partTextState.status === "ready" &&
                        !contextSegments ? (
                          <div className="neutral-notice" role="alert">
                            <p>
                              The recorded section span falls outside the
                              served CFR part text.
                            </p>
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
}
