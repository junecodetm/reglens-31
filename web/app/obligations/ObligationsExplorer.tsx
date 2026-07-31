"use client";

import { useEffect, useId, useRef, useState } from "react";

import { DocumentPicker } from "../components/DocumentPicker";
import { RejectedDetailPane } from "../components/RejectedDetailPane";
import { ReviewMemoPanel } from "../components/ReviewMemoPanel";
import {
  type ClaimRecord,
  type DocumentExtraction,
  type GroundingData,
  type RejectedDetailsData,
  type SiteData,
  type SourceTextState,
} from "../components/reglens-types";
import { SourcePane } from "../components/SourcePane";
import { useLazyJson } from "../components/ui/useLazyJson";
import {
  filterClaims,
  resolveReviewPart,
} from "./obligation-filters";

type PageDataState =
  | { status: "loading" }
  | {
      status: "ready";
      site: SiteData;
      documents: DocumentExtraction[];
    }
  | { status: "error"; message: string };

type ClaimView = "accepted" | "rejected";

export const CLAIM_PREVIEW_LIMIT = 25;

interface ObligationsExplorerProps {
  standalone?: boolean;
  initialView?: ClaimView;
}

async function fetchData<T>(
  path: string,
  signal: AbortSignal,
): Promise<T> {
  const response = await fetch(path, { signal });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

export function ObligationsExplorer({
  standalone = false,
  initialView = "accepted",
}: ObligationsExplorerProps) {
  const [pageData, setPageData] = useState<PageDataState>({
    status: "loading",
  });
  const [selectedDocumentNumber, setSelectedDocumentNumber] =
    useState("");
  const [view, setView] = useState<ClaimView>(initialView);
  const [selectedClaim, setSelectedClaim] = useState<ClaimRecord | null>(
    null,
  );
  const [showAllClaims, setShowAllClaims] = useState(false);
  const [obligationTypeFilter, setObligationTypeFilter] = useState("");
  const [affectedPartyFilter, setAffectedPartyFilter] = useState("");
  const [filterText, setFilterText] = useState("");
  const [sourceState, setSourceState] = useState<SourceTextState>({
    status: "idle",
  });
  const obligationTypeFilterId = useId();
  const affectedPartyFilterId = useId();
  const filterTextId = useId();
  const explorerRef = useRef<HTMLDivElement>(null);
  const sourceCacheRef = useRef<Map<string, string>>(new Map());
  const { state: rejectedDetailsState, load: loadRejectedDetails } =
    useLazyJson<RejectedDetailsData>("/data/rejected-details.json");
  const { state: groundingState, load: loadGroundingData } =
    useLazyJson<GroundingData>("/data/grounding.json");
  const selectedClaimDocumentNumber =
    selectedClaim?.document_number ?? null;
  const groundingData =
    groundingState.status === "ready" ? groundingState.data : null;
  const reviewPart = resolveReviewPart(
    selectedDocumentNumber,
    groundingData,
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadPageData() {
      try {
        const [site, documents] = await Promise.all([
          fetchData<SiteData>("/data/site.json", controller.signal),
          fetchData<DocumentExtraction[]>(
            "/data/claims.json",
            controller.signal,
          ),
        ]);

        if (!controller.signal.aborted) {
          setPageData({ status: "ready", site, documents });
        }
      } catch (error: unknown) {
        if (!controller.signal.aborted) {
          setPageData({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "The static snapshot could not be loaded.",
          });
        }
      }
    }

    void loadPageData();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (window.location.hash === "#rejected") {
      setView("rejected");
    }
  }, []);

  useEffect(() => {
    if (pageData.status !== "ready") {
      return;
    }

    setSelectedDocumentNumber((current) => {
      if (
        current &&
        pageData.documents.some(
          (document) => document.document_number === current,
        )
      ) {
        return current;
      }

      return (
        pageData.documents.find(
          (document) => document.document_number === "31-CFR-223",
        )?.document_number ??
        pageData.documents[0]?.document_number ??
        ""
      );
    });
  }, [pageData]);

  useEffect(() => {
    setSelectedClaim(null);
    setShowAllClaims(false);
  }, [selectedDocumentNumber, view]);

  useEffect(() => {
    setObligationTypeFilter("");
    setAffectedPartyFilter("");
    setFilterText("");
  }, [selectedDocumentNumber]);

  useEffect(() => {
    if (
      selectedDocumentNumber === "" ||
      resolveReviewPart(selectedDocumentNumber, null) !== null
    ) {
      return;
    }

    void loadGroundingData();
  }, [loadGroundingData, selectedDocumentNumber]);

  useEffect(() => {
    if (
      selectedClaim === null ||
      !window.matchMedia("(max-width: 47.99rem)").matches
    ) {
      return;
    }

    const destination =
      explorerRef.current?.querySelector<HTMLElement>(".source-pane");

    if (destination === undefined || destination === null) {
      return;
    }

    const bounds = destination.getBoundingClientRect();
    const isInViewport =
      bounds.top < window.innerHeight && bounds.bottom > 0;

    if (isInViewport) {
      return;
    }

    const prefersReducedMotion =
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    destination.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
      block: "start",
    });
    destination.focus({ preventScroll: true });
  }, [selectedClaim]);

  useEffect(() => {
    if (view === "rejected") {
      void loadRejectedDetails();
    }
  }, [loadRejectedDetails, view]);

  useEffect(() => {
    if (!selectedClaimDocumentNumber) {
      setSourceState({ status: "idle" });
      return;
    }

    const documentNumber = selectedClaimDocumentNumber;
    const cachedSource = sourceCacheRef.current.get(documentNumber);

    if (cachedSource !== undefined) {
      setSourceState({
        status: "ready",
        documentNumber,
        text: cachedSource,
      });
      return;
    }

    const controller = new AbortController();
    let isActive = true;

    setSourceState({
      status: "loading",
      documentNumber,
    });

    async function loadSourceText() {
      try {
        const response = await fetch(
          `/data/documents/${encodeURIComponent(documentNumber)}.txt`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          throw new Error(
            `The source request failed with status ${response.status}.`,
          );
        }

        const text = await response.text();

        if (isActive) {
          sourceCacheRef.current.set(documentNumber, text);
          setSourceState({
            status: "ready",
            documentNumber,
            text,
          });
        }
      } catch (error: unknown) {
        if (isActive && !controller.signal.aborted) {
          setSourceState({
            status: "error",
            documentNumber,
            message:
              error instanceof Error
                ? error.message
                : "The source document could not be loaded.",
          });
        }
      }
    }

    void loadSourceText();

    return () => {
      isActive = false;
      controller.abort();
    };
  }, [selectedClaimDocumentNumber]);

  const ErrorHeading = standalone ? "h2" : "h3";

  if (pageData.status === "loading") {
    return (
      <div className="loading-state page-state" role="status">
        Loading the pre-computed regulatory snapshot…
      </div>
    );
  }

  if (pageData.status === "error") {
    return (
      <div className="error-state page-state" role="alert">
        <ErrorHeading>Snapshot unavailable</ErrorHeading>
        <p>
          The pre-computed data files could not be loaded.{" "}
          {pageData.message}
        </p>
      </div>
    );
  }

  const selectedDocument =
    pageData.documents.find(
      (document) =>
        document.document_number === selectedDocumentNumber,
    ) ?? null;
  const acceptedCount = selectedDocument?.accepted_count ?? 0;
  const rejectedCount = selectedDocument?.rejected_count ?? 0;
  const allDocumentClaims = selectedDocument?.claims ?? [];
  const statusClaims =
    selectedDocument?.claims.filter((claim) =>
      view === "accepted" ? claim.accepted : !claim.accepted,
    ) ?? [];
  const obligationTypes = Array.from(
    new Set(allDocumentClaims.map((claim) => claim.obligation_type)),
  ).sort((left, right) => left.localeCompare(right));
  const affectedPartiesByKey = new Map<string, string>();

  for (const claim of allDocumentClaims) {
    const normalizedParty = claim.affected_party.trim().toLowerCase();

    if (!affectedPartiesByKey.has(normalizedParty)) {
      affectedPartiesByKey.set(normalizedParty, claim.affected_party);
    }
  }

  const affectedParties = Array.from(affectedPartiesByKey.values()).sort(
    (left, right) =>
      left.localeCompare(right, undefined, { sensitivity: "base" }),
  );
  const filteredClaims = filterClaims(
    allDocumentClaims,
    view,
    obligationTypeFilter,
    affectedPartyFilter,
    filterText,
  );
  const displayedClaims = showAllClaims
    ? filteredClaims
    : filteredClaims.slice(0, CLAIM_PREVIEW_LIMIT);
  const claimListId = `obligations-${view}-claims-list`;

  function resetClaimSelectionAndPreview(): void {
    setSelectedClaim(null);
    setShowAllClaims(false);
  }

  function selectDocument(documentNumber: string): void {
    resetClaimSelectionAndPreview();
    setObligationTypeFilter("");
    setAffectedPartyFilter("");
    setFilterText("");
    setSelectedDocumentNumber(documentNumber);
  }

  function selectView(nextView: ClaimView): void {
    resetClaimSelectionAndPreview();
    setView(nextView);
  }

  return (
    <div className="two-pane-grid" ref={explorerRef}>
      <section
        className="pane claims-pane"
        aria-label={standalone ? "Extracted obligations" : undefined}
        aria-labelledby={
          standalone ? undefined : "obligations-claims-heading"
        }
      >
        {!standalone ? (
          <h3 id="obligations-claims-heading">
            Extracted obligations
          </h3>
        ) : null}

        <DocumentPicker
          documents={pageData.documents}
          selectedDocumentNumber={selectedDocumentNumber}
          onSelect={selectDocument}
        />

        {reviewPart !== null ? (
          <ReviewMemoPanel part={reviewPart} compact />
        ) : null}

        <div
          className="view-toggle"
          role="group"
          aria-label="Claim status"
        >
          <button
            type="button"
            aria-pressed={view === "accepted"}
            onClick={() => selectView("accepted")}
          >
            Accepted ({acceptedCount})
          </button>
          <button
            type="button"
            aria-pressed={view === "rejected"}
            onClick={() => selectView("rejected")}
          >
            Rejected ({rejectedCount})
          </button>
        </div>

        <div className="margin-bottom-2">
          <label className="usa-label" htmlFor={obligationTypeFilterId}>
            Obligation type
          </label>
          <select
            className="usa-select"
            id={obligationTypeFilterId}
            value={obligationTypeFilter}
            onChange={(event) => {
              setObligationTypeFilter(event.target.value);
              resetClaimSelectionAndPreview();
            }}
          >
            <option value="">All types</option>
            {obligationTypes.map((obligationType) => (
              <option value={obligationType} key={obligationType}>
                {obligationType}
              </option>
            ))}
          </select>

          <label className="usa-label" htmlFor={affectedPartyFilterId}>
            Affected party
          </label>
          <select
            className="usa-select"
            id={affectedPartyFilterId}
            value={affectedPartyFilter}
            onChange={(event) => {
              setAffectedPartyFilter(event.target.value);
              resetClaimSelectionAndPreview();
            }}
          >
            <option value="">All parties</option>
            {affectedParties.map((affectedParty) => (
              <option
                value={affectedParty}
                key={affectedParty.trim().toLowerCase()}
              >
                {affectedParty}
              </option>
            ))}
          </select>

          <label className="usa-label" htmlFor={filterTextId}>
            Filter text
          </label>
          <input
            className="usa-input"
            id={filterTextId}
            type="search"
            value={filterText}
            onChange={(event) => {
              setFilterText(event.target.value);
              resetClaimSelectionAndPreview();
            }}
          />
        </div>

        <p className="margin-top-0" role="status">
          {displayedClaims.length} of {filteredClaims.length} shown
        </p>

        <div className="document-groups">
          {filteredClaims.length === 0 ? (
            <p className="empty-state">
              {statusClaims.length === 0
                ? `No ${view} claims are recorded for this document.`
                : `No ${view} claims match the selected filters.`}
            </p>
          ) : (
            <>
              <ul className="claim-list" id={claimListId}>
                {displayedClaims.map((claim) => {
                  const isSelected =
                    claim.claim_id === selectedClaim?.claim_id;

                  return (
                    <li key={claim.claim_id}>
                      <button
                        type="button"
                        className="claim-button"
                        aria-pressed={isSelected}
                        onClick={() => setSelectedClaim(claim)}
                      >
                        <span className="claim-button-topline">
                          <span className="claim-summary">
                            {claim.summary}
                          </span>
                          {isSelected ? (
                            <span
                              className="selected-indicator"
                              aria-hidden="true"
                            >
                              Selected
                            </span>
                          ) : null}
                        </span>

                        <span className="claim-metadata">
                          <span
                            className="obligation-tag"
                            data-obligation-type={claim.obligation_type}
                          >
                            {claim.obligation_type}
                          </span>
                          <span>
                            <span className="metadata-label">
                              Affected party:
                            </span>{" "}
                            {claim.affected_party}
                          </span>
                          {claim.effective_date ? (
                            <span>
                              <span className="metadata-label">
                                Effective:
                              </span>{" "}
                              <time dateTime={claim.effective_date}>
                                {claim.effective_date}
                              </time>
                            </span>
                          ) : null}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>

              {filteredClaims.length > CLAIM_PREVIEW_LIMIT ? (
                <button
                  type="button"
                  className="usa-button usa-button--outline"
                  aria-expanded={showAllClaims}
                  aria-controls={claimListId}
                  onClick={() =>
                    setShowAllClaims((current) => !current)
                  }
                >
                  {showAllClaims
                    ? `Show fewer ${view} claims`
                    : `Show all ${filteredClaims.length} ${view} claims`}
                </button>
              ) : null}
            </>
          )}
        </div>
      </section>

      {view === "accepted" ? (
        <SourcePane
          selectedClaim={selectedClaim}
          sourceState={sourceState}
          standalone={standalone}
        />
      ) : (
        <RejectedDetailPane
          selectedClaim={selectedClaim}
          sourceState={sourceState}
          detailsState={rejectedDetailsState}
          standalone={standalone}
        />
      )}
    </div>
  );
}
