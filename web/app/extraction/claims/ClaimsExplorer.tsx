"use client";

import { useEffect, useRef, useState } from "react";

import { ClaimsPane } from "../../components/ClaimsPane";
import {
  type ClaimRecord,
  type DocumentExtraction,
  type SiteData,
  type SourceTextState,
} from "../../components/reglens-types";
import { SourcePane } from "../../components/SourcePane";

type PageDataState =
  | { status: "loading" }
  | { status: "ready"; site: SiteData; documents: DocumentExtraction[] }
  | { status: "error"; message: string };

interface ClaimsExplorerProps {
  standalone?: boolean;
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

export function ClaimsExplorer({
  standalone = false,
}: ClaimsExplorerProps) {
  const [pageData, setPageData] = useState<PageDataState>({
    status: "loading",
  });
  const [selectedClaim, setSelectedClaim] = useState<ClaimRecord | null>(
    null,
  );
  const [sourceState, setSourceState] = useState<SourceTextState>({
    status: "idle",
  });
  const sourceCacheRef = useRef<Map<string, string>>(new Map());
  const selectedDocumentNumber = selectedClaim?.document_number ?? null;

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
    if (!selectedDocumentNumber) {
      setSourceState({ status: "idle" });
      return;
    }

    const documentNumber = selectedDocumentNumber;
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
  }, [selectedDocumentNumber]);

  const ErrorHeading = standalone ? "h2" : "h3";

  return (
    <>
      {pageData.status === "loading" ? (
        <div className="loading-state page-state" role="status">
          Loading the pre-computed regulatory snapshot…
        </div>
      ) : null}

      {pageData.status === "error" ? (
        <div className="error-state page-state" role="alert">
          <ErrorHeading>Snapshot unavailable</ErrorHeading>
          <p>
            The pre-computed data files could not be loaded.{" "}
            {pageData.message}
          </p>
        </div>
      ) : null}

      {pageData.status === "ready" ? (
        <div className="two-pane-grid">
          <ClaimsPane
            documents={pageData.documents}
            selectedClaimId={selectedClaim?.claim_id ?? null}
            onSelectClaim={setSelectedClaim}
            standalone={standalone}
          />
          <SourcePane
            selectedClaim={selectedClaim}
            sourceState={sourceState}
            standalone={standalone}
          />
        </div>
      ) : null}
    </>
  );
}
