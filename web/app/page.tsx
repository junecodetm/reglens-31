"use client";

import { useEffect, useRef, useState } from "react";

import { ClaimsPane } from "./components/ClaimsPane";
import { DisclaimerBand } from "./components/DisclaimerBand";
import { RejectedClaims } from "./components/RejectedClaims";
import { SourcePane } from "./components/SourcePane";
import {
  DISCLAIMER_TEXT,
  type ClaimRecord,
  type DocumentExtraction,
  type SiteData,
  type SourceTextState,
} from "./components/reglens-types";

type PageDataState =
  | { status: "loading" }
  | { status: "ready"; site: SiteData; documents: DocumentExtraction[] }
  | { status: "error"; message: string };

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

export default function Home() {
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

  const site = pageData.status === "ready" ? pageData.site : null;

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="site-header">
        <div className="content-bound header-content">
          <div className="title-block">
            <h1>RegLens-31</h1>
            <p>
              Provenance-gated regulatory obligation extraction — every claim
              verified verbatim against its primary source, fail-closed.
            </p>
          </div>

          <dl className="header-stats" aria-label="Snapshot totals">
            <div className="stat-badge stat-badge-accepted">
              <dt className="screen-reader-only">Accepted claims</dt>
              <dd>
                <strong>{site?.accepted_count ?? "—"}</strong> obligations
                verified
              </dd>
            </div>
            <div className="stat-badge stat-badge-rejected">
              <dt className="screen-reader-only">Rejected claims</dt>
              <dd>
                <strong>{site?.rejected_count ?? "—"}</strong> claims rejected
                by the provenance gate
              </dd>
            </div>
          </dl>
        </div>
      </header>

      <DisclaimerBand />

      <main id="main-content" className="content-bound main-content" tabIndex={-1}>
        {pageData.status === "loading" ? (
          <div className="loading-state page-state" role="status">
            Loading the pre-computed regulatory snapshot…
          </div>
        ) : null}

        {pageData.status === "error" ? (
          <div className="error-state page-state" role="alert">
            <h2>Snapshot unavailable</h2>
            <p>
              The pre-computed data files could not be loaded. {pageData.message}
            </p>
          </div>
        ) : null}

        {pageData.status === "ready" ? (
          <>
            <div className="two-pane-grid">
              <ClaimsPane
                documents={pageData.documents}
                selectedClaimId={selectedClaim?.claim_id ?? null}
                onSelectClaim={setSelectedClaim}
              />
              <SourcePane
                selectedClaim={selectedClaim}
                sourceState={sourceState}
              />
            </div>

            <RejectedClaims
              documents={pageData.documents}
              rejectedCount={pageData.site.rejected_count}
            />
          </>
        ) : null}
      </main>

      <footer className="site-footer">
        <div className="content-bound footer-content">
          <p>{DISCLAIMER_TEXT}</p>
          {site ? (
            <>
              <p>
                Data as of{" "}
                <time dateTime={site.data_as_of}>{site.data_as_of}</time> —
                pre-computed static snapshot; no live backend, no API keys.
              </p>
              <p>
                Extraction: {site.model_tags.join(", ")} running locally at
                temperature 0.
              </p>
            </>
          ) : (
            <p>Snapshot metadata is loading or unavailable.</p>
          )}
          <p>Source data: Federal Register (U.S. public domain).</p>
          <p>
            <a href="https://github.com/junecodetm/reglens-31">
              Source code &amp; methodology
              <span aria-hidden="true"> ↗</span>
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
