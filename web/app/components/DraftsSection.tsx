"use client";

import { useEffect, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import type { ConformanceData } from "./reglens-types";
import { ExpandableGroup } from "./ui/ExpandableGroup";
import { useLazyJson } from "./ui/useLazyJson";
import { useLazyTextMap } from "./ui/useLazyText";

type DraftChecklist = ConformanceData["checklists"][number];

interface DraftsSectionProps {
  active: boolean;
  standalone?: boolean;
}

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

function Checklist({
  checklist,
  standalone,
}: {
  checklist: DraftChecklist;
  standalone: boolean;
}) {
  const checklistChecks = [
    ["Headings in order", checklist.headings_in_order, "conformance"],
    [
      "Analysis sections present",
      checklist.analysis_sections_present,
      "conformance",
    ],
    ["Placeholders intact", checklist.placeholders_intact, "conformance"],
    [
      "Amendatory instructions parse",
      checklist.amendatory_instructions_parse,
      "conformance",
    ],
    ["Set-out text verified", checklist.setout_text_verified, "conformance"],
    [
      "Narrative fabrication clean",
      checklist.narrative_fabrication_clean,
      "conformance",
    ],
    ["Quotes verified", checklist.quotes_verified, "conformance"],
    ["Overall passed", checklist.passed, "conformance"],
    [
      "Authority citation present",
      checklist.authority_citation_present,
      "apa",
    ],
    [
      "Basis-and-purpose elements present",
      checklist.basis_and_purpose_present,
      "apa",
    ],
    [
      "Comment-period / effective-date reference",
      checklist.comment_period_reference,
      "apa",
    ],
    [
      "Amendatory verb forms demonstrated (add / revise / remove-and-reserve)",
      checklist.amendatory_forms_demonstrated,
      "apa",
    ],
  ] as const;
  // The aggregate "Overall passed" row stays in the itemized list but is
  // excluded from the summary count so a single real failure is not
  // double-counted through the aggregate.
  const substantiveChecks = checklistChecks.filter(
    ([label]) => label !== "Overall passed",
  );
  const summary = {
    passed: substantiveChecks.filter(([, value]) => value).length,
    total: substantiveChecks.length,
  };
  const Subheading = standalone ? "h3" : "h5";

  return (
    <div className="draft-checklist">
      <p className="draft-checklist-summary">
        <strong>
          {`${summary.passed}/${summary.total} checks passed`}
        </strong>
      </p>

      <details className="draft-checklist-details">
        <summary>Show itemized checklist</summary>
        <p>
          <strong>Conformance checklist</strong>
        </p>
        <ul
          className="eval-details"
          aria-label={`Conformance checklist for ${draftLabel(checklist)}`}
        >
          {checklistChecks
            .filter(([, , group]) => group === "conformance")
            .map(([label, value]) => (
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

        <Subheading>
          APA procedural elements (structural presence only)
        </Subheading>
        <ul
          className="eval-details"
          aria-label={`APA procedural elements for ${draftLabel(checklist)}`}
        >
          {checklistChecks
            .filter(([, , group]) => group === "apa")
            .map(([label, value]) => (
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
      </details>
    </div>
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

export function DraftsSection({
  active,
  standalone = false,
}: DraftsSectionProps) {
  const {
    state: conformanceState,
    load: loadConformance,
  } = useLazyJson<ConformanceData>("/data/conformance.json", {
    requestErrorPrefix: "Request failed with status ",
    fallbackErrorMessage: "The draft conformance data could not be loaded.",
  });
  const {
    stateFor: stateForDraft,
    load: requestDraftText,
  } = useLazyTextMap<string>({
    requestErrorPrefix: "Request failed with status ",
    fallbackErrorMessage: "The draft text could not be loaded.",
  });
  const [expandedDrafts, setExpandedDrafts] = useState<Set<string>>(
    () => new Set(),
  );

  useEffect(() => {
    if (active) {
      void loadConformance();
    }
  }, [active, loadConformance]);

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
      void requestDraftText(
        key,
        `/data/drafts/31-CFR-${encodeURIComponent(String(checklist.part))}-${encodeURIComponent(checklist.doc_type)}.txt`,
      );
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
  const InternalHeading = standalone ? "h2" : "h4";

  return (
    <section
      className="eval-section drafts-section"
      aria-label={standalone ? "Draft rule skeletons" : undefined}
      aria-labelledby={standalone ? undefined : "drafts-heading"}
    >
      {!standalone ? <h3 id="drafts-heading">Draft rule skeletons</h3> : null}

      <div id="drafts-section-panel">
        {conformanceState.status === "loading" ? (
          <p role="status">Loading draft conformance data…</p>
        ) : null}

        {conformanceState.status === "error" ? (
          <div role="alert">
            <InternalHeading>Draft data unavailable</InternalHeading>
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
                const draftTextState = stateForDraft(key);

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
                        <InternalHeading id={headingId}>
                          {label}
                        </InternalHeading>

                        {expanded ? (
                          <Button
                            type="button"
                            outline
                            className="width-full text-left"
                            aria-label={`Hide draft text for ${label}`}
                            aria-expanded={expanded}
                            aria-controls={togglePanelId}
                            onClick={onToggle}
                          >Hide draft text</Button>
                        ) : (
                          <Button
                            type="button"
                            outline
                            className="width-full text-left"
                            aria-label={`Load and show draft text for ${label}`}
                            aria-expanded={expanded}
                            aria-controls={togglePanelId}
                            onClick={onToggle}
                          >Load and show draft text</Button>
                        )}
                      </>
                    )}
                    beforePanel={
                      <>
                        <Checklist
                          checklist={checklist}
                          standalone={standalone}
                        />
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
                <InternalHeading>Rejected drafts</InternalHeading>
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
