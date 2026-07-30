"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import { groupAuthoritySections } from "./crossref-utils";
import type { AuthorityData } from "./reglens-types";
import { ExpandableGroup } from "./ui/ExpandableGroup";
import {
  HighlightedText,
  type HighlightedTextProps,
} from "./ui/HighlightedText";
import { useLazyJson } from "./ui/useLazyJson";

type AuthorityPart = AuthorityData["parts"][number];
type AuthorityCitation = AuthorityPart["citations"][number];
type ResolvedSection = AuthorityPart["resolved"][number];
type CitationKind = AuthorityCitation["kind"];
type NonSectionCitationKind = Exclude<CitationKind, "usc-section">;

type TextLoadState =
  | { status: "idle" }
  | { status: "loading"; key: string }
  | { status: "ready"; key: string; text: string }
  | { status: "error"; key: string; message: string };

interface UscSelection {
  part: number;
  title: number;
  section: string;
}

interface TextRequestViewProps
  extends Omit<HighlightedTextProps, "text"> {
  state: TextLoadState;
  requestKey: string;
  loadingMessage: string;
}

const CITATION_KINDS: readonly CitationKind[] = [
  "usc-section",
  "usc-note",
  "public-law",
  "executive-order",
];

const NON_SECTION_KINDS: readonly NonSectionCitationKind[] = [
  "usc-note",
  "public-law",
  "executive-order",
];

const CITATION_KIND_LABELS: Record<CitationKind, string> = {
  "usc-section": "U.S.C. sections",
  "usc-note": "U.S.C. notes",
  "public-law": "Public laws",
  "executive-order": "Executive orders",
};

const NEUTRAL_NOTICE_CLASS =
  "bg-base-lightest border border-base-lighter radius-sm padding-2 text-ink";
const NEUTRAL_COUNT_CLASS =
  "bg-base-lightest border border-base-lighter radius-sm padding-1 text-ink";
const CLASSIFICATION_CHIP_CLASS =
  "usa-tag bg-base-lighter text-ink text-normal";

function domIdSegment(value: string): string {
  return value.replace(/[^A-Za-z0-9_-]/g, "-");
}

function authorityPartKey(part: number): string {
  return String(part);
}

function uscTextKey(title: number, section: string): string {
  return `${title}:${section}`;
}

function isSameUscSelection(
  selected: UscSelection | null,
  part: number,
  section: ResolvedSection,
): boolean {
  return (
    selected?.part === part &&
    selected.title === section.usc_title &&
    selected.section === section.usc_section
  );
}

function findCitationForSection(
  part: AuthorityPart,
  section: ResolvedSection,
): AuthorityCitation | undefined {
  return part.citations.find(
    (citation) =>
      citation.kind === "usc-section" &&
      citation.usc_title === section.usc_title &&
      citation.usc_section === section.usc_section,
  );
}

async function fetchText(
  path: string,
  signal: AbortSignal,
): Promise<string> {
  const response = await fetch(path, { signal });

  if (!response.ok) {
    throw new Error(`The text request returned status ${response.status}.`);
  }

  return response.text();
}

function TextRequestView({
  state,
  requestKey,
  loadingMessage,
  ...highlightedTextProps
}: TextRequestViewProps) {
  if (state.status === "idle" || state.key !== requestKey) {
    return null;
  }

  if (state.status === "loading") {
    return (
      <p className="loading-state" role="status">
        {loadingMessage}
      </p>
    );
  }

  if (state.status === "error") {
    return (
      <div
        className={`${NEUTRAL_NOTICE_CLASS} margin-top-1`}
        role="alert"
      >
        <p className="margin-y-0">
          <strong>Text unavailable.</strong> {state.message}
        </p>
      </div>
    );
  }

  return (
    <HighlightedText
      text={state.text}
      {...highlightedTextProps}
      descriptionId={`authority-text-status-${domIdSegment(highlightedTextProps.selectionKey)}`}
      readyStatusClassName="screen-reader-only"
      noticeStatusClassName={`${NEUTRAL_NOTICE_CLASS} margin-top-1`}
      scrollBehavior="smooth"
      retryWhenVisible={false}
    />
  );
}

interface AuthorityPartDetailsProps {
  part: AuthorityPart;
  selectedUsc: UscSelection | null;
  uscTextState: TextLoadState;
  onToggleUsc: (part: number, section: ResolvedSection) => void;
  standalone: boolean;
}

interface AuthoritySectionProps {
  active: boolean;
  standalone?: boolean;
}

function AuthorityPartDetails({
  part,
  selectedUsc,
  uscTextState,
  onToggleUsc,
  standalone,
}: AuthorityPartDetailsProps) {
  const [expandedSilentRanges, setExpandedSilentRanges] = useState<
    Set<string>
  >(() => new Set());
  const nonSectionCount = part.citations.filter(
    (citation) => citation.kind !== "usc-section",
  ).length;
  const sectionGroups = groupAuthoritySections(part);
  const DetailHeading: "h3" | "h5" = standalone ? "h3" : "h5";
  const RangeHeading: "h4" | "h6" = standalone ? "h4" : "h6";

  function toggleSilentRange(range: string): void {
    setExpandedSilentRanges((current) => {
      const next = new Set(current);

      if (next.has(range)) {
        next.delete(range);
      } else {
        next.add(range);
      }

      return next;
    });
  }

  function renderSection(section: ResolvedSection) {
    const citation = findCitationForSection(part, section);
    const rawCitation =
      citation?.raw ??
      `${section.usc_title} U.S.C. ${section.usc_section}`;
    const uscIsSelected = isSameUscSelection(
      selectedUsc,
      part.part,
      section,
    );
    const textKey = uscTextKey(
      section.usc_title,
      section.usc_section,
    );
    const panelId = `authority-usc-${part.part}-${section.usc_title}-${domIdSegment(section.usc_section)}`;

    return (
      <ExpandableGroup
        as="li"
        id={panelId}
        label={
          <>
            <span className="display-block text-bold">
              {uscIsSelected
                ? "Hide U.S.C. section text"
                : "Show U.S.C. section text"}
            </span>
            <span className="display-block margin-top-1">
              {rawCitation}
            </span>
          </>
        }
        expanded={uscIsSelected}
        onToggle={() => onToggleUsc(part.part, section)}
        containerId={null}
        className={null}
        ariaLabelledby={null}
        panelId={panelId}
        panelClassName={null}
        renderToggle={({
          expanded,
          label,
          onToggle,
          panelId: controlledPanelId,
        }) => (
          <Button
            type="button"
            base
            outline
            className="width-full text-left"
            aria-expanded={expanded}
            aria-controls={controlledPanelId}
            onClick={onToggle}
          >
            {label}
          </Button>
        )}
        beforePanel={
          <div className="padding-x-1 padding-bottom-2">
            <p className="margin-y-1">
              <strong>Heading:</strong> {section.heading}
            </p>
            <p className="margin-y-1">
              <strong>Identifier:</strong>{" "}
              <code>{section.identifier}</code>
            </p>
            <p className="margin-y-1">
              <span className={CLASSIFICATION_CHIP_CLASS}>
                Classification: {section.classification}
              </span>
            </p>
            {section.status ? (
              <p className="margin-y-1">
                <strong>Status:</strong> {section.status}
              </p>
            ) : null}
            {citation?.from_range ? (
              <p className="margin-y-1">
                <strong>Expanded from cited range:</strong>{" "}
                {citation.from_range}
              </p>
            ) : null}
            <p className="margin-y-1">
              <strong>Recorded verb passage:</strong>{" "}
              {section.verb_quote ? (
                <q>{section.verb_quote}</q>
              ) : (
                "None recorded"
              )}
            </p>
            {section.gate_rejected ? (
              <div className={`${NEUTRAL_NOTICE_CLASS} margin-y-1`}>
                <p className="margin-y-0">
                  <strong>Gate rejection recorded.</strong>{" "}
                  {section.rejection_reason ?? "No reason is recorded."}
                </p>
              </div>
            ) : null}
          </div>
        }
        key={section.identifier}
      >
        <TextRequestView
          state={uscTextState}
          requestKey={textKey}
          loadingMessage={`Loading ${section.usc_title} U.S.C. ${section.usc_section} text…`}
          start={section.verb_start}
          end={section.verb_end}
          selectionKey={`usc-${part.part}-${textKey}`}
          regionLabel={`${section.usc_title} U.S.C. ${section.usc_section} text`}
          highlightStatus={`Recorded verb passage highlighted for ${section.usc_title} U.S.C. ${section.usc_section}.`}
          noSpanMessage="No verb passage span is recorded; the full U.S.C. section text is shown."
          boundsMessage="The recorded verb passage span falls outside the served U.S.C. section text; the full section text is shown without a highlighted passage."
        />
      </ExpandableGroup>
    );
  }

  return (
    <>
      <section className="margin-top-3">
        <DetailHeading id={`authority-part-${part.part}-usc-heading`}>
          {CITATION_KIND_LABELS["usc-section"]}
        </DetailHeading>

        {part.resolved.length === 0 ? (
          <p>No resolved U.S.C. sections are recorded.</p>
        ) : (
          <div>
            {sectionGroups.map((group, groupIndex) => {
              const rangeId = `authority-range-${part.part}-${groupIndex}`;
              const range = group.range;
              const silentSectionsAreExpanded =
                range !== null && expandedSilentRanges.has(range);

              return (
                <div
                  className={groupIndex === 0 ? undefined : "margin-top-3"}
                  key={range ?? "direct-citations"}
                >
                  {range !== null ? (
                    <RangeHeading
                      id={`${rangeId}-heading`}
                      className="margin-bottom-1"
                    >
                      Cited range: {range}
                    </RangeHeading>
                  ) : null}

                  <ul className="claim-list">
                    {group.visibleSections.map(renderSection)}

                    {range !== null && group.silentSections.length > 0 ? (
                      <ExpandableGroup
                        as="li"
                        id={rangeId}
                        label={
                          silentSectionsAreExpanded
                            ? `${group.silentSections.length} of ${group.sections.length} sections in this range have no mandatory or discretionary classification and no recorded language — hide them`
                            : `${group.silentSections.length} of ${group.sections.length} sections in this range have no mandatory or discretionary classification and no recorded language — show them`
                        }
                        expanded={silentSectionsAreExpanded}
                        onToggle={() => toggleSilentRange(range)}
                        containerId={null}
                        className={null}
                        panelClassName={null}
                        renderToggle={({
                          expanded,
                          label,
                          onToggle,
                          buttonId,
                          panelId,
                        }) => (
                          <Button
                            id={buttonId}
                            type="button"
                            outline
                            className="width-full text-left"
                            aria-expanded={expanded}
                            aria-controls={panelId}
                            onClick={onToggle}
                          >
                            {label}
                          </Button>
                        )}
                      >
                        <ul className="claim-list margin-top-2">
                          {group.silentSections.map(renderSection)}
                        </ul>
                      </ExpandableGroup>
                    ) : null}
                  </ul>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="margin-top-3">
        <DetailHeading id={`authority-part-${part.part}-coverage-heading`}>
          Resolves outside codified section text (coverage category)
        </DetailHeading>

        {nonSectionCount === 0 ? (
          <p>None recorded for this part.</p>
        ) : (
          NON_SECTION_KINDS.map((kind) => {
            const citations = part.citations.filter(
              (citation) => citation.kind === kind,
            );

            if (citations.length === 0) {
              return null;
            }

            return (
              <section key={kind}>
                <DetailHeading
                  id={`authority-part-${part.part}-${kind}-heading`}
                >
                  {CITATION_KIND_LABELS[kind]}
                </DetailHeading>
                <ul className="usa-list">
                  {citations.map((citation, index) => (
                    <li key={`${citation.raw}-${index}`}>{citation.raw}</li>
                  ))}
                </ul>
              </section>
            );
          })
        )}
      </section>

      <section className="margin-top-3">
        <DetailHeading id={`authority-part-${part.part}-unresolved-heading`}>
          Unresolved (fail-closed, not guessed)
        </DetailHeading>

        {part.unresolved.length === 0 ? (
          <p>None recorded for this part.</p>
        ) : (
          CITATION_KINDS.map((kind) => {
            const citations = part.unresolved.filter(
              (citation) => citation.kind === kind,
            );

            if (citations.length === 0) {
              return null;
            }

            return (
              <section key={kind}>
                <DetailHeading
                  id={`authority-part-${part.part}-unresolved-${kind}-heading`}
                >
                  {CITATION_KIND_LABELS[kind]}
                </DetailHeading>
                <ul className="usa-list">
                  {citations.map((citation, index) => (
                    <li key={`${citation.raw}-${index}`}>
                      {citation.raw}
                      {citation.from_range ? (
                        <> (from range {citation.from_range})</>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </section>
            );
          })
        )}
      </section>
    </>
  );
}

export function AuthoritySection({
  active,
  standalone = false,
}: AuthoritySectionProps) {
  const { state: authorityState, load: loadAuthorityData } =
    useLazyJson<AuthorityData>("/data/authority.json", {
      requestErrorPrefix: "The authority request returned status ",
      fallbackErrorMessage: "The authority data could not be loaded.",
    });
  const [selectedPart, setSelectedPart] = useState<number | null>(null);
  const [partTextState, setPartTextState] = useState<TextLoadState>({
    status: "idle",
  });
  const [selectedUsc, setSelectedUsc] = useState<UscSelection | null>(
    null,
  );
  const [uscTextState, setUscTextState] = useState<TextLoadState>({
    status: "idle",
  });

  const partControllerRef = useRef<AbortController | null>(null);
  const uscControllerRef = useRef<AbortController | null>(null);
  const partTextCacheRef = useRef<Map<string, string>>(new Map());
  const uscTextCacheRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    if (active) {
      void loadAuthorityData();
    }
  }, [active, loadAuthorityData]);

  useEffect(() => {
    return () => {
      partControllerRef.current?.abort();
      uscControllerRef.current?.abort();
    };
  }, []);

  async function loadPartText(part: number): Promise<void> {
    const key = authorityPartKey(part);

    if (
      partTextState.status === "loading" &&
      partTextState.key === key
    ) {
      return;
    }

    partControllerRef.current?.abort();
    partControllerRef.current = null;

    const cached = partTextCacheRef.current.get(key);

    if (cached !== undefined) {
      setPartTextState({ status: "ready", key, text: cached });
      return;
    }

    const controller = new AbortController();
    partControllerRef.current = controller;
    setPartTextState({ status: "loading", key });

    try {
      const text = await fetchText(
        `/data/authority-parts/31-CFR-${encodeURIComponent(String(part))}.txt`,
        controller.signal,
      );

      if (!controller.signal.aborted) {
        partTextCacheRef.current.set(key, text);
        setPartTextState({ status: "ready", key, text });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setPartTextState({
          status: "error",
          key,
          message:
            error instanceof Error
              ? error.message
              : "The part text could not be loaded.",
        });
      }
    } finally {
      if (partControllerRef.current === controller) {
        partControllerRef.current = null;
      }
    }
  }

  async function loadUscText(
    title: number,
    section: string,
  ): Promise<void> {
    const key = uscTextKey(title, section);

    if (uscTextState.status === "loading" && uscTextState.key === key) {
      return;
    }

    uscControllerRef.current?.abort();
    uscControllerRef.current = null;

    const cached = uscTextCacheRef.current.get(key);

    if (cached !== undefined) {
      setUscTextState({ status: "ready", key, text: cached });
      return;
    }

    const controller = new AbortController();
    uscControllerRef.current = controller;
    setUscTextState({ status: "loading", key });

    try {
      const text = await fetchText(
        `/data/usc/usc-${encodeURIComponent(String(title))}-s${encodeURIComponent(section)}.txt`,
        controller.signal,
      );

      if (!controller.signal.aborted) {
        uscTextCacheRef.current.set(key, text);
        setUscTextState({ status: "ready", key, text });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setUscTextState({
          status: "error",
          key,
          message:
            error instanceof Error
              ? error.message
              : "The U.S.C. section text could not be loaded.",
        });
      }
    } finally {
      if (uscControllerRef.current === controller) {
        uscControllerRef.current = null;
      }
    }
  }

  function togglePart(part: number): void {
    if (selectedPart === part) {
      setSelectedPart(null);
      return;
    }

    setSelectedPart(part);
    void loadPartText(part);
  }

  function toggleUsc(part: number, section: ResolvedSection): void {
    if (isSameUscSelection(selectedUsc, part, section)) {
      setSelectedUsc(null);
      return;
    }

    setSelectedUsc({
      part,
      title: section.usc_title,
      section: section.usc_section,
    });
    void loadUscText(section.usc_title, section.usc_section);
  }

  const PartHeading: "h2" | "h4" = standalone ? "h2" : "h4";

  return (
    <section
      className="rejected-section authority-section"
      aria-labelledby={standalone ? undefined : "authority-heading"}
      aria-label={standalone ? "Statutory authority" : undefined}
    >
      {standalone ? null : (
        <h3 id="authority-heading">Statutory authority</h3>
      )}

      <div id="authority-section-content">
        {authorityState.status === "loading" ? (
          <p className="loading-state" role="status">
            Loading statutory authority data…
          </p>
        ) : null}

        {authorityState.status === "error" ? (
          <div
            className={`${NEUTRAL_NOTICE_CLASS} margin-top-2`}
            role="alert"
          >
            <p className="margin-y-0">
              <strong>Statutory authority data unavailable.</strong>{" "}
              {authorityState.message}
            </p>
          </div>
        ) : null}

        {authorityState.status === "ready" ? (
          <>
            <dl
              className="display-flex flex-wrap gap-1 margin-y-2"
              aria-label="Statutory authority totals"
            >
              <div className={NEUTRAL_COUNT_CLASS}>
                <dt className="screen-reader-only">Resolved sections</dt>
                <dd className="margin-0">
                  <strong>{authorityState.data.total_resolved}</strong>{" "}
                  resolved
                </dd>
              </div>
              <div className={NEUTRAL_COUNT_CLASS}>
                <dt className="screen-reader-only">Unresolved citations</dt>
                <dd className="margin-0">
                  <strong>{authorityState.data.total_unresolved}</strong>{" "}
                  unresolved
                </dd>
              </div>
              <div className={NEUTRAL_COUNT_CLASS}>
                <dt className="screen-reader-only">
                  Non-section citations
                </dt>
                <dd className="margin-0">
                  <strong>
                    {authorityState.data.total_non_section_citations}
                  </strong>{" "}
                  non-section
                </dd>
              </div>
              <div
                className={`${NEUTRAL_COUNT_CLASS} authority-gate-count bg-base-lighter`}
              >
                <dt className="screen-reader-only">Gate rejections</dt>
                <dd className="margin-0">
                  <strong>{authorityState.data.gate_rejections}</strong>{" "}
                  gate rejections
                </dd>
              </div>
            </dl>

            <div className="document-groups">
              {authorityState.data.parts.map((part) => {
                const partIsSelected = selectedPart === part.part;
                const partKey = authorityPartKey(part.part);
                const partPanelId = `authority-part-${part.part}-text`;

                return (
                  <ExpandableGroup
                    id={`authority-part-${part.part}`}
                    label={`31 CFR part ${part.part}: ${part.part_heading}`}
                    expanded={partIsSelected}
                    onToggle={() => togglePart(part.part)}
                    containerId={null}
                    className="document-group"
                    ariaLabelledby={null}
                    panelId={partPanelId}
                    panelClassName={null}
                    renderToggle={({
                      expanded,
                      label,
                      onToggle,
                      panelId,
                    }) => (
                      <>
                        <PartHeading>{label}</PartHeading>

                        <Button
                          type="button"
                          base
                          outline
                          className="width-full text-left"
                          aria-expanded={expanded}
                          aria-controls={panelId}
                          onClick={onToggle}
                        >
                          <span className="display-block text-bold margin-bottom-1">
                            {expanded ? "Hide part text" : "Show part text"}
                          </span>
                          <span className="display-block">
                            {part.authority_text}
                          </span>
                        </Button>
                      </>
                    )}
                    afterPanel={
                      <AuthorityPartDetails
                        part={part}
                        selectedUsc={selectedUsc}
                        uscTextState={uscTextState}
                        onToggleUsc={toggleUsc}
                        standalone={standalone}
                      />
                    }
                    key={part.part}
                  >
                    <TextRequestView
                      state={partTextState}
                      requestKey={partKey}
                      loadingMessage={`Loading 31 CFR part ${part.part} text…`}
                      start={part.authority_start}
                      end={part.authority_end}
                      selectionKey={`part-${part.part}`}
                      regionLabel={`31 CFR part ${part.part} text`}
                      highlightStatus={`Authority citation passage highlighted for 31 CFR part ${part.part}.`}
                      noSpanMessage="No authority citation span is recorded; the full part text is shown."
                      boundsMessage="The recorded authority citation span falls outside the served part text; the full part text is shown without a highlighted passage."
                    />

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
