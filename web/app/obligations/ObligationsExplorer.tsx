"use client";

import { useEffect, useRef, useState } from "react";

import { DocumentPicker } from "../components/DocumentPicker";
import { RejectedDetailPane } from "../components/RejectedDetailPane";
import {
  type ClaimRecord,
  type DocumentExtraction,
  type RejectedDetailsData,
  type SiteData,
  type SourceTextState,
} from "../components/reglens-types";
import { SourcePane } from "../components/SourcePane";
import { useLazyJson } from "../components/ui/useLazyJson";

type PageDataState =
  | { status: "loading" }
  | {
      status: "ready";
      site: SiteData;
      documents: DocumentExtraction[];
    }
  | { status: "error"; message: string };

type ClaimView = "accepted" | "rejected";

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
  const [sourceState, setSourceState] = useState<SourceTextState>({
    status: "idle",
  });
  const sourceCacheRef = useRef<Map<string, string>>(new Map());
  const { state: rejectedDetailsState, load: loadRejectedDetails } =
    useLazyJson<RejectedDetailsData>("/data/rejected-details.json");
  const selectedClaimDocumentNumber =
    selectedClaim?.document_number ?? null;

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
  }, [selectedDocumentNumber, view]);

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
  const visibleClaims =
    selectedDocument?.claims.filter((claim) =>
      view === "accepted" ? claim.accepted : !claim.accepted,
    ) ?? [];

  function selectDocument(documentNumber: string): void {
    setSelectedClaim(null);
    setSelectedDocumentNumber(documentNumber);
  }

  function selectView(nextView: ClaimView): void {
    setSelectedClaim(null);
    setView(nextView);
  }

  return (
    <div className="two-pane-grid">
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

        <div className="document-groups">
          {visibleClaims.length === 0 ? (
            <p className="empty-state">
              No {view} claims are recorded for this document.
            </p>
          ) : (
            <ul className="claim-list">
              {visibleClaims.map((claim) => {
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
