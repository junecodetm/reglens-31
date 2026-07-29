"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import type { ConformanceData } from "./reglens-types";
import { ExpandableGroup } from "./ui/ExpandableGroup";
import { useLazyJson } from "./ui/useLazyJson";

type DraftTextState =
  | { status: "loading" }
  | { status: "ready"; text: string }
  | { status: "error"; message: string };

type DraftChecklist = ConformanceData["checklists"][number];

function draftKey(checklist: DraftChecklist): string {
  return `${checklist.part}-${checklist.doc_type}`;
}

function draftLabel(checklist: DraftChecklist): string {
  const documentType =
    checklist.doc_type === "nprm"
      ? "Notice of proposed rulemaking"
      : "Final rule";

  return `31 CFR Part ${checklist.part} — ${documentType}`;
}

function passFail(value: boolean): "pass" | "fail" {
  return value ? "pass" : "fail";
}

function formatPassRate(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function Checklist({ checklist }: { checklist: DraftChecklist }) {
  const booleanChecks = [
    ["Headings in order", checklist.headings_in_order],
    ["Analysis sections present", checklist.analysis_sections_present],
    ["Placeholders intact", checklist.placeholders_intact],
    [
      "Amendatory instructions parse",
      checklist.amendatory_instructions_parse,
    ],
    ["Set-out text verified", checklist.setout_text_verified],
    [
      "Narrative fabrication clean",
      checklist.narrative_fabrication_clean,
    ],
    ["Quotes verified", checklist.quotes_verified],
    ["Overall passed", checklist.passed],
  ] as const;
  const apaProceduralChecks = [
    ["Authority citation present", checklist.authority_citation_present],
    [
      "Basis-and-purpose elements present",
      checklist.basis_and_purpose_present,
    ],
    [
      "Comment-period / effective-date reference",
      checklist.comment_period_reference,
    ],
    [
      "Amendatory verb forms demonstrated (add / revise / remove-and-reserve)",
      checklist.amendatory_forms_demonstrated,
    ],
  ] as const;

  return (
    <>
      <p>
        <strong>Conformance checklist</strong>
      </p>
      <ul
        className="eval-details"
        aria-label={`Conformance checklist for ${draftLabel(checklist)}`}
      >
        {booleanChecks.map(([label, value]) => (
          <li key={label}>
            {label}: <strong>{passFail(value)}</strong>
          </li>
        ))}
        <li>Unverified quote count: {checklist.unverified_quote_count}</li>
        <li>
          Fabrication hits:{" "}
          {checklist.fabrication_hits.length === 0
            ? "none"
            : checklist.fabrication_hits.join("; ")}
        </li>
      </ul>

      <h4>APA procedural elements (structural presence only)</h4>
      <ul
        className="eval-details"
        aria-label={`APA procedural elements for ${draftLabel(checklist)}`}
      >
        {apaProceduralChecks.map(([label, value]) => (
          <li key={label}>
            {label}: <strong>{passFail(value)}</strong>
          </li>
        ))}
      </ul>
      <p>
        {
          "These checks verify the structural presence of required elements in the skeleton. They are not a determination of legal sufficiency."
        }
      </p>
    </>
  );
}

function GenerationProvenance({
  checklist,
}: {
  checklist: DraftChecklist;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const key = draftKey(checklist);
  const buttonId = `draft-${key}-provenance-button`;
  const panelId = `draft-${key}-provenance-panel`;

  return (
    <div>
      <Button
        id={buttonId}
        type="button"
        base
        outline
        aria-expanded={isExpanded}
        aria-controls={panelId}
        onClick={() => setIsExpanded((current) => !current)}
      >
        Generation provenance
      </Button>

      <div id={panelId} aria-labelledby={buttonId} hidden={!isExpanded}>
        <p>
          <strong>Model:</strong> {checklist.dossier.model}
        </p>
        <p>
          <strong>Decoding:</strong> temperature{" "}
          {checklist.dossier.temperature}, seed {checklist.dossier.seed}, context{" "}
          {checklist.dossier.num_ctx}, max tokens{" "}
          {checklist.dossier.num_predict}
        </p>
        <p>
          <strong>System prompt SHA-256:</strong>{" "}
          <code className="provenance-digest">
            {checklist.dossier.system_prompt_sha256}
          </code>
        </p>
        <p>
          <strong>User prompt SHA-256:</strong>{" "}
          <code className="provenance-digest">
            {checklist.dossier.prompt_sha256}
          </code>
        </p>
        <p>
          <strong>Source part snapshot SHA-256 (context of record; not sent to the model):</strong>{" "}
          <code className="provenance-digest">
            {checklist.dossier.input_sha256}
          </code>
        </p>
        <p>
          <strong>Model-generated fields:</strong>{" "}
          {checklist.dossier.narrative_fields.join(", ")}
        </p>
        <p>
          {
            "Model, decoding parameters, and SHA-256 digests of the prompts sent to the model and of the source part snapshot of record. Everything else in the skeleton is deterministic template output."
          }
        </p>
      </div>
    </div>
  );
}

export function DraftsSection() {
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    state: conformanceState,
    load: loadConformance,
  } = useLazyJson<ConformanceData>("/data/conformance.json", {
    requestErrorPrefix: "Request failed with status ",
    fallbackErrorMessage: "The draft conformance data could not be loaded.",
  });
  const [expandedDrafts, setExpandedDrafts] = useState<Set<string>>(
    () => new Set(),
  );
  const [draftTextStates, setDraftTextStates] = useState<
    Record<string, DraftTextState>
  >({});
  const draftRequestsRef = useRef<Set<string>>(new Set());
  const draftControllersRef = useRef<Map<string, AbortController>>(
    new Map(),
  );

  useEffect(() => {
    return () => {
      draftControllersRef.current.forEach((controller) => controller.abort());
    };
  }, []);

  async function loadDraft(checklist: DraftChecklist, key: string) {
    const draftTextState = draftTextStates[key];

    if (
      (draftTextState !== undefined && draftTextState.status !== "error") ||
      draftRequestsRef.current.has(key)
    ) {
      return;
    }

    const controller = new AbortController();
    draftRequestsRef.current.add(key);
    draftControllersRef.current.set(key, controller);
    setDraftTextStates((current) => ({
      ...current,
      [key]: { status: "loading" },
    }));

    try {
      const response = await fetch(
        `/data/drafts/31-CFR-${encodeURIComponent(String(checklist.part))}-${encodeURIComponent(checklist.doc_type)}.txt`,
        { signal: controller.signal },
      );

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}.`);
      }

      const text = await response.text();

      if (!controller.signal.aborted) {
        setDraftTextStates((current) => ({
          ...current,
          [key]: { status: "ready", text },
        }));
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setDraftTextStates((current) => ({
          ...current,
          [key]: {
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "The draft text could not be loaded.",
          },
        }));
      }
    } finally {
      draftRequestsRef.current.delete(key);
      draftControllersRef.current.delete(key);
    }
  }

  function handleSectionToggle() {
    const willExpand = !isExpanded;
    setIsExpanded(willExpand);

    if (
      willExpand &&
      (conformanceState.status === "idle" ||
        conformanceState.status === "error")
    ) {
      void loadConformance();
    }
  }

  function handleDraftToggle(checklist: DraftChecklist) {
    const key = draftKey(checklist);
    const willExpand = !expandedDrafts.has(key);

    setExpandedDrafts((current) => {
      const next = new Set(current);

      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }

      return next;
    });

    if (willExpand) {
      void loadDraft(checklist, key);
    }
  }

  const sortedChecklists =
    conformanceState.status === "ready"
      ? [...conformanceState.data.checklists].sort(
          (left, right) =>
            left.part - right.part ||
            left.doc_type.localeCompare(right.doc_type),
        )
      : [];

  return (
    <section
      className="eval-section drafts-section"
      aria-labelledby="drafts-heading"
    >
      <h2 id="drafts-heading">Draft rule skeletons</h2>

      <Button
        type="button"
        base
        outline
        aria-expanded={isExpanded}
        aria-controls="drafts-section-panel"
        onClick={handleSectionToggle}
      >
        {isExpanded
          ? "Collapse draft rule skeletons"
          : "Expand draft rule skeletons"}
      </Button>

      <div id="drafts-section-panel" hidden={!isExpanded}>
        {conformanceState.status === "loading" ? (
          <p role="status">Loading draft conformance data…</p>
        ) : null}

        {conformanceState.status === "error" ? (
          <div role="alert">
            <h3>Draft data unavailable</h3>
            <p>
              The draft conformance data could not be loaded.{" "}
              {conformanceState.message}
            </p>
          </div>
        ) : null}

        {conformanceState.status === "ready" ? (
          <>
            <dl className="metric-grid" aria-label="Draft conformance totals">
              <div className="metric-card">
                <dt>Accepted / generated</dt>
                <dd className="metric-value">
                  {conformanceState.data.accepted} /{" "}
                  {conformanceState.data.generated}
                </dd>
              </div>
              <div className="metric-card">
                <dt>Pass rate</dt>
                <dd className="metric-value">
                  {formatPassRate(conformanceState.data.pass_rate)}
                </dd>
              </div>
              <div className="metric-card">
                <dt>Total unverified quotes</dt>
                <dd className="metric-value">
                  {conformanceState.data.total_unverified_quotes}
                </dd>
              </div>
            </dl>

            <p className="model-generated-note">
              <strong>Model note:</strong> {conformanceState.data.model_note}
            </p>

            <div className="document-groups">
              {sortedChecklists.map((checklist) => {
                const key = draftKey(checklist);
                const label = draftLabel(checklist);
                const headingId = `draft-${key}-heading`;
                const panelId = `draft-${key}-panel`;
                const draftIsExpanded = expandedDrafts.has(key);
                const draftTextState = draftTextStates[key];

                return (
                  <ExpandableGroup
                    id={`draft-${key}`}
                    label={label}
                    expanded={draftIsExpanded}
                    onToggle={() => handleDraftToggle(checklist)}
                    as="article"
                    containerId={null}
                    className="document-group"
                    ariaLabelledby={headingId}
                    panelId={panelId}
                    panelClassName={null}
                    key={key}
                    renderToggle={({
                      expanded,
                      onToggle,
                      panelId: togglePanelId,
                    }) => (
                      <>
                        <h3 id={headingId}>{label}</h3>

                        <Button
                          type="button"
                          base
                          outline
                          aria-expanded={expanded}
                          aria-controls={togglePanelId}
                          onClick={onToggle}
                          style={{ width: "100%", textAlign: "left" }}
                        >
                          {expanded
                            ? `Hide draft text for ${label}`
                            : `Load and show draft text for ${label}`}
                        </Button>
                      </>
                    )}
                    beforePanel={
                      <>
                        <Checklist checklist={checklist} />
                        <GenerationProvenance checklist={checklist} />
                      </>
                    }
                  >
                    {draftTextState?.status === "loading" ? (
                      <p role="status">Loading draft text for {label}…</p>
                    ) : null}

                    {draftTextState?.status === "error" ? (
                      <p role="alert">
                        The draft text could not be loaded.{" "}
                        {draftTextState.message}
                      </p>
                    ) : null}

                    {draftTextState?.status === "ready" ? (
                      <pre
                        className="source-document"
                        tabIndex={0}
                        role="region"
                        aria-label={`Draft text for ${label}`}
                      >
                        {draftTextState.text}
                      </pre>
                    ) : null}
                  </ExpandableGroup>
                );
              })}
            </div>

            {conformanceState.data.rejected_drafts.length > 0 ? (
              <div>
                <h3>Rejected drafts</h3>
                <ul>
                  {conformanceState.data.rejected_drafts.map((draft) => (
                    <li key={draft}>{draft}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}
