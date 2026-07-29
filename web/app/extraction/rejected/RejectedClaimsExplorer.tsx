"use client";

import { useEffect } from "react";

import { RejectedClaims } from "../../components/RejectedClaims";
import {
  type DocumentExtraction,
  type SiteData,
} from "../../components/reglens-types";
import { useLazyJson } from "../../components/ui/useLazyJson";

export function RejectedClaimsExplorer() {
  const { state: siteState, load: loadSite } =
    useLazyJson<SiteData>("/data/site.json");
  const { state: documentsState, load: loadDocuments } =
    useLazyJson<DocumentExtraction[]>("/data/claims.json");

  useEffect(() => {
    void loadSite();
    void loadDocuments();
  }, [loadDocuments, loadSite]);

  if (
    siteState.status === "idle" ||
    siteState.status === "loading" ||
    documentsState.status === "idle" ||
    documentsState.status === "loading"
  ) {
    return (
      <div className="loading-state page-state" role="status">
        Loading the pre-computed regulatory snapshot…
      </div>
    );
  }

  if (
    siteState.status === "error" ||
    documentsState.status === "error"
  ) {
    const message =
      siteState.status === "error"
        ? siteState.message
        : documentsState.status === "error"
          ? documentsState.message
          : "The static snapshot could not be loaded.";

    return (
      <div className="error-state page-state" role="alert">
        <h3>Snapshot unavailable</h3>
        <p>
          The pre-computed data files could not be loaded. {message}
        </p>
      </div>
    );
  }

  return (
    <RejectedClaims
      documents={documentsState.data}
      rejectedCount={siteState.data.rejected_count}
    />
  );
}
