"use client";

import {
  Fragment,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Button, Table } from "@trussworks/react-uswds";

import type { GroundingData } from "./reglens-types";
import {
  computeHighlightSegments,
  HighlightedText,
} from "./ui/HighlightedText";
import { useLazyJson } from "./ui/useLazyJson";

const BAND_DEFINITION =
  "Bands report TEXTUAL-MARKER DENSITY only (listed phrase families per 1,000 words; none=0, low≤0.2, moderate≤0.6, elevated>0.6), applied identically to both marker families. They describe phrase frequency in the published document text and are not a prediction of any judicial outcome or a statement about any regulation's validity.";

type GroundingRule = GroundingData["rules"][number];
type GroundingMarker = GroundingRule["markers"][number];

type DocumentViewState =
  | { status: "idle" }
  | { status: "loading"; documentNumber: string }
  | { status: "ready"; documentNumber: string; text: string }
  | { status: "error"; documentNumber: string; message: string };

interface SelectedMarker {
  documentNumber: string;
  markerIndex: number;
  marker: GroundingMarker;
}

interface GroundingSectionProps {
  active: boolean;
  standalone?: boolean;
}

function compareDocumentNumbers(
  first: GroundingRule,
  second: GroundingRule,
): number {
  if (first.document_number < second.document_number) {
    return -1;
  }
  if (first.document_number > second.document_number) {
    return 1;
  }
  return 0;
}

function yesNoDash(value: boolean | null): string {
  if (value === null) {
    return "-";
  }
  return value ? "yes" : "no";
}

function toDomId(value: string): string {
  return value.replace(/[^A-Za-z0-9_-]/g, "-");
}

function DensityValue({
  count,
  band,
}: {
  count: number;
  band: GroundingRule["deference_band"];
}) {
  return (
    <span
      className="display-inline-block bg-base-lighter text-ink padding-x-1 padding-y-05 radius-sm"
      style={{ minWidth: "9.5rem" }}
    >
      <span className="text-bold">{count}</span>{" "}
      <span>{band} textual-marker density</span>
    </span>
  );
}

export function GroundingSection({
  active,
  standalone = false,
}: GroundingSectionProps) {
  const { state: groundingState, load: loadGroundingData } =
    useLazyJson<GroundingData>("/data/grounding.json", {
      requestErrorPrefix: "Request returned status ",
      fallbackErrorMessage: "The grounding data could not be loaded.",
    });
  const [expandedRuleNumber, setExpandedRuleNumber] = useState<string | null>(
    null,
  );
  const [selectedMarker, setSelectedMarker] =
    useState<SelectedMarker | null>(null);
  const [documentView, setDocumentView] = useState<DocumentViewState>({
    status: "idle",
  });

  const documentCacheRef = useRef<Map<string, string>>(new Map());
  const documentControllersRef = useRef<Map<string, AbortController>>(
    new Map(),
  );
  const selectedMarkerRef = useRef<SelectedMarker | null>(null);

  const sortedRules = useMemo(() => {
    if (groundingState.status !== "ready") {
      return [];
    }
    return [...groundingState.data.rules].sort(compareDocumentNumbers);
  }, [groundingState]);
  const displayedBandDefinition =
    groundingState.status === "ready"
      ? groundingState.data.band_definition
      : BAND_DEFINITION;

  const readyText =
    selectedMarker !== null &&
    documentView.status === "ready" &&
    documentView.documentNumber === selectedMarker.documentNumber
      ? documentView.text
      : null;
  const highlightResult =
    selectedMarker !== null && readyText !== null
      ? computeHighlightSegments(
          readyText,
          selectedMarker.marker.start,
          selectedMarker.marker.end,
        )
      : null;
  const selectedMarkerKey =
    selectedMarker === null
      ? null
      : `${selectedMarker.documentNumber}-${selectedMarker.markerIndex}-${selectedMarker.marker.start}-${selectedMarker.marker.end}`;

  useEffect(() => {
    if (active) {
      void loadGroundingData();
    }
  }, [active, loadGroundingData]);

  useEffect(() => {
    const documentControllers = documentControllersRef.current;

    return () => {
      for (const controller of documentControllers.values()) {
        controller.abort();
      }
      documentControllers.clear();
    };
  }, []);

  function clearSelectedMarker() {
    selectedMarkerRef.current = null;
    setSelectedMarker(null);
    setDocumentView({ status: "idle" });
  }

  function toggleRule(documentNumber: string) {
    if (expandedRuleNumber === documentNumber) {
      setExpandedRuleNumber(null);
      clearSelectedMarker();
      return;
    }

    setExpandedRuleNumber(documentNumber);
    clearSelectedMarker();
  }

  async function loadDocument(selection: SelectedMarker) {
    const documentNumber = selection.documentNumber;
    const cachedText = documentCacheRef.current.get(documentNumber);
    if (cachedText !== undefined) {
      setDocumentView({
        status: "ready",
        documentNumber,
        text: cachedText,
      });
      return;
    }

    const pendingController =
      documentControllersRef.current.get(documentNumber);
    if (pendingController) {
      setDocumentView({ status: "loading", documentNumber });
      return;
    }

    const controller = new AbortController();
    documentControllersRef.current.set(documentNumber, controller);
    setDocumentView({ status: "loading", documentNumber });

    try {
      const response = await fetch(
        `/data/documents/${encodeURIComponent(documentNumber)}.txt`,
        { signal: controller.signal },
      );
      if (!response.ok) {
        throw new Error(`Request returned status ${response.status}.`);
      }

      const text = await response.text();
      documentCacheRef.current.set(documentNumber, text);

      if (
        !controller.signal.aborted &&
        selectedMarkerRef.current?.documentNumber === documentNumber
      ) {
        setDocumentView({ status: "ready", documentNumber, text });
      }
    } catch (error: unknown) {
      if (
        !controller.signal.aborted &&
        selectedMarkerRef.current?.documentNumber === documentNumber
      ) {
        setDocumentView({
          status: "error",
          documentNumber,
          message:
            error instanceof Error
              ? error.message
              : "The published document text could not be loaded.",
        });
      }
    } finally {
      if (
        documentControllersRef.current.get(documentNumber) === controller
      ) {
        documentControllersRef.current.delete(documentNumber);
      }
    }
  }

  function toggleMarker(
    rule: GroundingRule,
    marker: GroundingMarker,
    markerIndex: number,
  ) {
    const isSelected =
      selectedMarker?.documentNumber === rule.document_number &&
      selectedMarker.markerIndex === markerIndex;

    if (isSelected) {
      clearSelectedMarker();
      return;
    }

    const selection: SelectedMarker = {
      documentNumber: rule.document_number,
      markerIndex,
      marker,
    };
    selectedMarkerRef.current = selection;
    setSelectedMarker(selection);
    void loadDocument(selection);
  }

  const InternalHeading: "h2" | "h4" = standalone ? "h2" : "h4";
  const NestedHeading: "h3" | "h4" = standalone ? "h3" : "h4";

  return (
    <section
      className="grounding-section margin-top-5 padding-top-2 border-top-1px border-base-lighter"
      aria-label={
        standalone ? "Grounding markers (two-sided)" : undefined
      }
      aria-labelledby={standalone ? undefined : "grounding-heading"}
    >
      {!standalone ? (
        <h3 id="grounding-heading">
          Grounding markers (two-sided)
        </h3>
      ) : null}

      <div
        className="bg-base-lightest border-left-05 border-base padding-2 margin-bottom-2"
        role="note"
        aria-label="Textual-marker density definition"
      >
        <p className="margin-y-0">{displayedBandDefinition}</p>
      </div>

      <div
        id="grounding-content"
        className="margin-top-2"
      >
        {groundingState.status === "idle" ||
        groundingState.status === "loading" ? (
          <p role="status">Loading grounding data…</p>
        ) : null}

        {groundingState.status === "error" ? (
          <div
            className="bg-base-lightest border-2px border-base padding-2 radius-md"
            role="alert"
          >
            <InternalHeading className="margin-top-0">
              Grounding data unavailable
            </InternalHeading>
            <p className="margin-bottom-0">{groundingState.message}</p>
          </div>
        ) : null}

        {groundingState.status === "ready" ? (
          <>
            <p>
              Rule records: {sortedRules.length}. Gate rejections:{" "}
              {groundingState.data.total_gate_rejections}. Table order:
              document number.
            </p>

            <Table
              bordered
              compact
              fullWidth
              scrollable
              caption="Published rule records ordered lexicographically by document number. Both textual-marker density band columns use identical styling."
            >
              <thead>
                <tr>
                  <th scope="col">Document number</th>
                  <th scope="col">Title</th>
                  <th scope="col">Publication date</th>
                  <th scope="col">
                    Deference count and textual-marker density band
                  </th>
                  <th scope="col">
                    Grounding count and textual-marker density band
                  </th>
                  <th scope="col">Predates Loper Bright</th>
                  <th scope="col">Cites Chevron</th>
                  <th scope="col">Marker details</th>
                </tr>
              </thead>
              <tbody>
                {sortedRules.map((rule) => {
                  const ruleId = toDomId(rule.document_number);
                  const markerContentId = `grounding-markers-${ruleId}`;
                  const ruleExpanded =
                    expandedRuleNumber === rule.document_number;

                  return (
                    <Fragment key={rule.document_number}>
                      <tr>
                        <th scope="row">{rule.document_number}</th>
                        <td>
                          <span
                            title={rule.title}
                            style={{
                              display: "block",
                              maxWidth: "18rem",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {rule.title}
                          </span>
                        </td>
                        <td>
                          <time dateTime={rule.publication_date}>
                            {rule.publication_date}
                          </time>
                        </td>
                        <td>
                          <DensityValue
                            count={rule.deference_count}
                            band={rule.deference_band}
                          />
                        </td>
                        <td>
                          <DensityValue
                            count={rule.grounding_count}
                            band={rule.grounding_band}
                          />
                        </td>
                        <td>{yesNoDash(rule.predates_loper_bright)}</td>
                        <td>{yesNoDash(rule.cites_chevron)}</td>
                        <td>
                          <Button
                            type="button"
                            unstyled
                            aria-expanded={ruleExpanded}
                            aria-controls={markerContentId}
                            onClick={() => toggleRule(rule.document_number)}
                          >
                            {ruleExpanded ? "Hide" : "Show"}{" "}
                            {rule.markers.length}{" "}
                            {rule.markers.length === 1 ? "marker" : "markers"}
                            <span className="screen-reader-only">
                              {" "}
                              for document {rule.document_number}
                            </span>
                          </Button>
                        </td>
                      </tr>
                      <tr hidden={!ruleExpanded}>
                        <td
                          colSpan={8}
                          className="bg-base-lightest padding-2"
                        >
                          <div id={markerContentId}>
                            <InternalHeading className="margin-top-0">
                              Markers for document {rule.document_number}
                            </InternalHeading>

                            {rule.markers.length === 0 ? (
                              <p>No markers were recorded for this document.</p>
                            ) : (
                              <ul className="usa-list usa-list--unstyled">
                                {rule.markers.map((marker, markerIndex) => {
                                  const markerSelected =
                                    selectedMarker?.documentNumber ===
                                      rule.document_number &&
                                    selectedMarker.markerIndex === markerIndex;
                                  const markerPanelId = `grounding-source-${ruleId}-${markerIndex}`;

                                  return (
                                    <li
                                      key={`${marker.start}-${marker.end}-${markerIndex}`}
                                      className="border-bottom-1px border-base-lighter padding-y-2"
                                    >
                                      <p className="margin-y-0">
                                        <strong>Family:</strong> {marker.family}
                                        <br />
                                        <strong>Side:</strong> {marker.side}
                                      </p>
                                      <blockquote className="margin-y-1">
                                        <code
                                          style={{ whiteSpace: "pre-wrap" }}
                                        >
                                          {marker.quote}
                                        </code>
                                      </blockquote>
                                      <Button
                                        type="button"
                                        unstyled
                                        aria-expanded={markerSelected}
                                        aria-controls={markerPanelId}
                                        onClick={() =>
                                          toggleMarker(
                                            rule,
                                            marker,
                                            markerIndex,
                                          )
                                        }
                                      >
                                        {markerSelected ? "Hide" : "Show"}{" "}
                                        published document text
                                        <span className="screen-reader-only">
                                          {" "}
                                          for marker {markerIndex + 1} in
                                          document {rule.document_number}
                                        </span>
                                      </Button>

                                      <div
                                        id={markerPanelId}
                                        hidden={!markerSelected}
                                        className="margin-top-2"
                                      >
                                        {markerSelected &&
                                        (documentView.status === "idle" ||
                                          documentView.status === "loading") ? (
                                          <p role="status">
                                            Loading published document text…
                                          </p>
                                        ) : null}

                                        {markerSelected &&
                                        documentView.status === "error" &&
                                        documentView.documentNumber ===
                                          rule.document_number ? (
                                          <div
                                            className="bg-base-lightest border-2px border-base padding-2 radius-md"
                                            role="alert"
                                          >
                                            <NestedHeading className="margin-top-0">
                                              Published document text
                                              unavailable
                                            </NestedHeading>
                                            <p className="margin-bottom-0">
                                              {documentView.message}
                                            </p>
                                          </div>
                                        ) : null}

                                        {markerSelected &&
                                        selectedMarker !== null &&
                                        readyText !== null ? (
                                          <>
                                            {highlightResult?.status ===
                                            "ready" ? (
                                              <p role="status">
                                                Highlighted saved marker span [
                                                {selectedMarker.marker.start},{" "}
                                                {selectedMarker.marker.end}) for
                                                family{" "}
                                                {
                                                  selectedMarker.marker
                                                    .family
                                                }
                                                .
                                              </p>
                                            ) : (
                                              <div
                                                className="bg-base-lightest border-2px border-base padding-2 radius-md"
                                                role="alert"
                                              >
                                                <NestedHeading className="margin-top-0">
                                                  Marker span unavailable
                                                </NestedHeading>
                                                <p className="margin-bottom-0">
                                                  The saved offsets do not fall
                                                  within the published document
                                                  text, so no passage is
                                                  highlighted.
                                                </p>
                                              </div>
                                            )}

                                            <HighlightedText
                                              text={readyText}
                                              start={
                                                selectedMarker.marker.start
                                              }
                                              end={selectedMarker.marker.end}
                                              selectionKey={
                                                selectedMarkerKey ??
                                                rule.document_number
                                              }
                                              regionLabel={`Published document text for ${rule.document_number}, marker ${markerIndex + 1}`}
                                              highlightStatus={`Highlighted saved marker span [${selectedMarker.marker.start}, ${selectedMarker.marker.end}) for family ${selectedMarker.marker.family}.`}
                                              noSpanMessage="The saved offsets do not fall within the published document text, so no passage is highlighted."
                                              boundsMessage="The saved offsets do not fall within the published document text, so no passage is highlighted."
                                              retryWhenVisible={false}
                                              showStatus={false}
                                            />
                                          </>
                                        ) : null}
                                      </div>
                                    </li>
                                  );
                                })}
                              </ul>
                            )}
                          </div>
                        </td>
                      </tr>
                    </Fragment>
                  );
                })}
              </tbody>
            </Table>

            <section aria-labelledby="grounding-coverage-heading">
              <InternalHeading id="grounding-coverage-heading">
                Coverage notes
              </InternalHeading>
              {groundingState.data.coverage_notes.length > 0 ? (
                <ul className="usa-list">
                  {groundingState.data.coverage_notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              ) : (
                <p>No coverage notes were supplied.</p>
              )}
            </section>
          </>
        ) : null}
      </div>
    </section>
  );
}
