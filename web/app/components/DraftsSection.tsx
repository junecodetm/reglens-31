"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Button } from "@trussworks/react-uswds";

import {
  assembleSkeleton,
  checkLiveDraft,
  type LiveDraftChecklist,
  requestLiveDraft,
} from "./draft-live";
import type { ConformanceData } from "./reglens-types";
import { ExpandableGroup } from "./ui/ExpandableGroup";
import { useLazyJson } from "./ui/useLazyJson";
import { useLazyTextMap } from "./ui/useLazyText";

type DraftChecklist = ConformanceData["checklists"][number];
type DraftDocType = DraftChecklist["doc_type"];

interface DraftInputs {
  parts: Array<{
    part: number;
    heading: string;
    authority: string;
  }>;
  doc_types: string[];
}

type LiveDraftState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "ready";
      assembled: string;
      checklist: LiveDraftChecklist;
      model: string;
    }
  | {
      status: "fallback";
      message: string;
      part: number;
      docType: DraftDocType;
    };

interface DraftsSectionProps {
  active: boolean;
  standalone?: boolean;
}

interface DraftParametersPanelProps {
  active: boolean;
  standalone: boolean;
  onShowCommittedDraft: (part: number, docType: DraftDocType) => void;
}

const LIVE_CHECKS = [
  ["Headings in order", "headings_in_order"],
  ["Analysis sections present", "analysis_sections_present"],
  ["Placeholders intact", "placeholders_intact"],
  ["Narrative fabrication clean", "narrative_fabrication_clean"],
  ["Quotes verified", "quotes_verified"],
] as const;

const RATE_LIMIT_NOTICE =
  "The shared free-tier generation limit is momentarily exhausted. The committed, fully conformance-gated draft for these parameters is shown instead.";
const UNAVAILABLE_NOTICE =
  "Live generation is unavailable. The committed, fully conformance-gated draft for these parameters is shown instead.";

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

function draftTextPath(part: number, docType: DraftDocType): string {
  return `/data/drafts/31-CFR-${encodeURIComponent(String(part))}-${encodeURIComponent(docType)}.txt`;
}

function draftTemplatePath(part: number, docType: DraftDocType): string {
  return `/data/draft-templates/31-CFR-${encodeURIComponent(String(part))}-${encodeURIComponent(docType)}.txt`;
}

function authorityPartPath(part: number): string {
  return `/data/authority-parts/31-CFR-${encodeURIComponent(String(part))}.txt`;
}

async function fetchPlainText(path: string): Promise<string> {
  const response = await fetch(path);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}.`);
  }

  return response.text();
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

function DraftParametersPanel({
  active,
  standalone,
  onShowCommittedDraft,
}: DraftParametersPanelProps) {
  const { state: inputState, load: loadInputs } =
    useLazyJson<DraftInputs>("/data/draft-inputs.json", {
      requestErrorPrefix: "Request failed with status ",
      fallbackErrorMessage: "The draft parameters could not be loaded.",
    });
  const [part, setPart] = useState<number | null>(null);
  const [docType, setDocType] = useState<DraftDocType>("nprm");
  const [policyGoal, setPolicyGoal] = useState("");
  const [liveResult, setLiveResult] = useState<LiveDraftState>({
    status: "idle",
  });
  const submissionRef = useRef(0);

  useEffect(() => {
    if (active) {
      void loadInputs();
    }
  }, [active, loadInputs]);

  useEffect(
    () => () => {
      submissionRef.current += 1;
    },
    [],
  );

  if (inputState.status !== "ready") {
    return null;
  }

  const supportedDocTypes = inputState.data.doc_types.filter(
    (value): value is DraftDocType =>
      value === "nprm" || value === "final",
  );
  const selectedPart =
    part !== null &&
    inputState.data.parts.some((item) => item.part === part)
      ? part
      : (inputState.data.parts[0]?.part ?? null);
  const selectedDocType = supportedDocTypes.includes(docType)
    ? docType
    : (supportedDocTypes[0] ?? null);
  const selectedPartRecord =
    inputState.data.parts.find((item) => item.part === selectedPart) ??
    null;
  const PanelHeading = standalone ? "h2" : "h4";

  function resetLiveResult(): void {
    submissionRef.current += 1;
    setLiveResult({ status: "idle" });
  }

  function showFallback(
    selectedPartValue: number,
    selectedDocTypeValue: DraftDocType,
    rateLimited: boolean,
  ): void {
    const message = rateLimited ? RATE_LIMIT_NOTICE : UNAVAILABLE_NOTICE;
    setLiveResult({
      status: "fallback",
      message,
      part: selectedPartValue,
      docType: selectedDocTypeValue,
    });
    onShowCommittedDraft(selectedPartValue, selectedDocTypeValue);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (selectedPart === null || selectedDocType === null) {
      return;
    }

    const submission = submissionRef.current + 1;
    submissionRef.current = submission;
    setLiveResult({ status: "loading" });

    const response = await requestLiveDraft(
      selectedPart,
      selectedDocType,
      policyGoal,
    );

    if (submissionRef.current !== submission) {
      return;
    }

    if (!response.ok) {
      showFallback(selectedPart, selectedDocType, response.rateLimited);
      return;
    }

    try {
      const [template, partText] = await Promise.all([
        fetchPlainText(draftTemplatePath(selectedPart, selectedDocType)),
        fetchPlainText(authorityPartPath(selectedPart)),
      ]);

      if (submissionRef.current !== submission) {
        return;
      }

      const assembled = assembleSkeleton(
        template,
        response.summary,
        response.supplementary_intro,
      );
      const checklist = checkLiveDraft(
        assembled,
        `${response.summary}\n${response.supplementary_intro}`,
        partText,
      );
      setLiveResult({
        status: "ready",
        assembled,
        checklist,
        model: response.model,
      });
    } catch {
      if (submissionRef.current === submission) {
        showFallback(selectedPart, selectedDocType, false);
      }
    }
  }

  const failedChecks =
    liveResult.status === "ready"
      ? LIVE_CHECKS.filter(
          ([, property]) => !liveResult.checklist[property],
        ).map(([label]) => label)
      : [];

  return (
    <section
      className="bg-base-lightest border border-base-lighter radius-md padding-2 margin-bottom-4"
      aria-labelledby="draft-parameters-heading"
    >
      <PanelHeading id="draft-parameters-heading" className="margin-top-0">
        Draft parameters
      </PanelHeading>

      <form onSubmit={handleSubmit}>
        <div className="grid-row grid-gap">
          <div className="tablet:grid-col-6">
            <label className="usa-label" htmlFor="draft-part">
              CFR part
            </label>
            <select
              className="usa-select"
              id="draft-part"
              name="draft-part"
              value={selectedPart ?? ""}
              onChange={(event) => {
                setPart(Number(event.currentTarget.value));
                resetLiveResult();
              }}
            >
              {inputState.data.parts.map((item) => (
                <option key={item.part} value={item.part}>
                  31 CFR part {item.part} — {item.heading}
                </option>
              ))}
            </select>
          </div>

          <fieldset className="usa-fieldset tablet:grid-col-6">
            <legend className="usa-legend">Document type</legend>
            <div className="usa-radio">
              <input
                className="usa-radio__input"
                id="draft-document-type-nprm"
                name="draft-document-type"
                type="radio"
                value="nprm"
                checked={selectedDocType === "nprm"}
                disabled={!supportedDocTypes.includes("nprm")}
                onChange={() => {
                  setDocType("nprm");
                  resetLiveResult();
                }}
              />
              <label
                className="usa-radio__label"
                htmlFor="draft-document-type-nprm"
              >
                NPRM
              </label>
            </div>
            <div className="usa-radio">
              <input
                className="usa-radio__input"
                id="draft-document-type-final"
                name="draft-document-type"
                type="radio"
                value="final"
                checked={selectedDocType === "final"}
                disabled={!supportedDocTypes.includes("final")}
                onChange={() => {
                  setDocType("final");
                  resetLiveResult();
                }}
              />
              <label
                className="usa-radio__label"
                htmlFor="draft-document-type-final"
              >
                Final rule
              </label>
            </div>
          </fieldset>
        </div>

        {selectedPartRecord ? (
          <p className="margin-top-2 margin-bottom-0">
            <strong>Authority:</strong> {selectedPartRecord.authority}
          </p>
        ) : null}

        <label className="usa-label" htmlFor="draft-policy-objective">
          Policy objective (optional)
        </label>
        <textarea
          className="usa-textarea"
          id="draft-policy-objective"
          name="draft-policy-objective"
          maxLength={500}
          value={policyGoal}
          aria-describedby="draft-policy-objective-count"
          onChange={(event) => {
            setPolicyGoal(event.currentTarget.value);
            resetLiveResult();
          }}
        />
        <p
          className="text-base-dark margin-top-05"
          id="draft-policy-objective-count"
        >
          {policyGoal.length} / 500 characters
        </p>

        <Button
          type="submit"
          disabled={
            selectedPart === null ||
            selectedDocType === null ||
            liveResult.status === "loading"
          }
        >
          Generate opening narrative (live)
        </Button>
      </form>

      <div className="margin-top-3" aria-live="polite">
        {liveResult.status === "loading" ? (
          <p>Generating the opening narrative…</p>
        ) : null}

        {liveResult.status === "fallback" ? (
          <div className="border border-base-lighter bg-base-lightest padding-2 radius-sm">
            <p className="margin-top-0">{liveResult.message}</p>
            <p className="margin-bottom-0">
              <a
                href={`#draft-${liveResult.part}-${liveResult.docType}`}
              >
                Go to the committed draft entry.
              </a>
            </p>
          </div>
        ) : null}

        {liveResult.status === "ready" ? (
          <>
            <p>
              Live model output ({liveResult.model}) — checked by the
              in-browser subset of the conformance gate. Not an agency
              document. Not legal advice.
            </p>
            <ul
              className="add-list-reset display-flex flex-wrap gap-1"
              aria-label="Live conformance subset checks"
            >
              {LIVE_CHECKS.map(([label, property]) => (
                <li key={property}>
                  <span className="usa-tag bg-base-lighter text-ink text-normal">
                    {label}: {passFail(liveResult.checklist[property])}
                  </span>
                </li>
              ))}
            </ul>
            {failedChecks.length > 0 ? (
              <div className="border-left-1 border-error padding-left-2 margin-top-2">
                <p>
                  <strong>Checks requiring review:</strong>{" "}
                  {failedChecks.join(", ")}.
                </p>
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      {liveResult.status === "ready" ? (
        <pre
          className="source-document"
          tabIndex={0}
          role="region"
          aria-label={`Live draft text generated by ${liveResult.model}`}
        >
          {liveResult.assembled}
        </pre>
      ) : null}
    </section>
  );
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
  const decodingKnobs = [
    ["temperature", checklist.dossier.temperature],
    ["seed", checklist.dossier.seed],
    ["context", checklist.dossier.num_ctx],
    ["prediction tokens", checklist.dossier.num_predict],
    ["max tokens", checklist.dossier.max_tokens],
    ["reasoning effort", checklist.dossier.reasoning_effort],
  ].filter(([, value]) => value !== null && value !== undefined);

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
        <dl>
          <div>
            <dt>Model</dt>
            <dd>{checklist.dossier.model}</dd>
          </div>
          <div>
            <dt>Provider</dt>
            <dd>{checklist.dossier.provider ?? "local"}</dd>
          </div>
          <div>
            <dt>Decoding</dt>
            <dd>
              {decodingKnobs
                .map(([label, value]) => `${label} ${String(value)}`)
                .join(", ")}
            </dd>
          </div>
          <div>
            <dt>System prompt SHA-256</dt>
            <dd>
              <code className="provenance-digest">
                {checklist.dossier.system_prompt_sha256}
              </code>
            </dd>
          </div>
          <div>
            <dt>User prompt SHA-256</dt>
            <dd>
              <code className="provenance-digest">
                {checklist.dossier.prompt_sha256}
              </code>
            </dd>
          </div>
          <div>
            <dt>
              Source part snapshot SHA-256 (context of record; not sent to the
              model)
            </dt>
            <dd>
              <code className="provenance-digest">
                {checklist.dossier.input_sha256}
              </code>
            </dd>
          </div>
          <div>
            <dt>Model-generated fields</dt>
            <dd>{checklist.dossier.narrative_fields.join(", ")}</dd>
          </div>
        </dl>
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

  const showCommittedDraft = useCallback(
    (part: number, docType: DraftDocType) => {
      const key = `${part}-${docType}`;

      setExpandedDrafts((current) => {
        if (current.has(key)) {
          return current;
        }

        const next = new Set(current);
        next.add(key);
        return next;
      });
      void requestDraftText(key, draftTextPath(part, docType));

      const hash = `#draft-${key}`;
      window.history.replaceState(null, "", hash);
      window.requestAnimationFrame(() => {
        const heading = document.getElementById(`draft-${key}-heading`);
        heading?.scrollIntoView({ behavior: "auto", block: "start" });
        heading?.focus({ preventScroll: true });
      });
    },
    [requestDraftText],
  );

  useEffect(() => {
    if (conformanceState.status !== "ready") {
      return;
    }

    const checklists = conformanceState.data.checklists;

    function showDraftFromHash(): void {
      const match = /^#draft-(\d+)-(nprm|final)$/.exec(
        window.location.hash,
      );

      if (!match) {
        return;
      }

      const part = Number(match[1]);
      const docType = match[2] as DraftDocType;

      if (
        checklists.some(
          (checklist) =>
            checklist.part === part && checklist.doc_type === docType,
        )
      ) {
        showCommittedDraft(part, docType);
      }
    }

    showDraftFromHash();
    window.addEventListener("hashchange", showDraftFromHash);

    return () => {
      window.removeEventListener("hashchange", showDraftFromHash);
    };
  }, [conformanceState, showCommittedDraft]);

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
        draftTextPath(checklist.part, checklist.doc_type),
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
        <DraftParametersPanel
          active={active}
          standalone={standalone}
          onShowCommittedDraft={showCommittedDraft}
        />

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
                    containerId={`draft-${key}`}
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
                        <InternalHeading id={headingId} tabIndex={-1}>
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
