"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { AboutSection } from "./components/AboutSection";
import { AuthoritySection } from "./components/AuthoritySection";
import { BrowseSection } from "./components/BrowseSection";
import { ClaimsPane } from "./components/ClaimsPane";
import { CrossRefSection } from "./components/CrossRefSection";
import { DisclaimerBand } from "./components/DisclaimerBand";
import { DraftsSection } from "./components/DraftsSection";
import { EvalSection } from "./components/EvalSection";
import { GroundingSection } from "./components/GroundingSection";
import { Ogc01EvalSection } from "./components/Ogc01EvalSection";
import { PageNav } from "./components/PageNav";
import { RejectedClaims } from "./components/RejectedClaims";
import { SearchSection } from "./components/SearchSection";
import { SourcePane } from "./components/SourcePane";
import {
  DISCLAIMER_TEXT,
  type ClaimRecord,
  type DocumentExtraction,
  type SiteData,
  type SourceTextState,
} from "./components/reglens-types";
import { CollapsibleSection } from "./components/ui/CollapsibleSection";

const HERO_MOCKUP_LINE =
  "An independent working mockup aligned to U.S. Treasury AI use case OGC-01 (“Regulatory Reform Tool,” Treasury public AI Use Case Inventory) — see About this demonstration below.";
const FOOTER_ATTRIBUTION =
  "Use-case framing: Treasury AI Use Case Inventory (U.S. Government work) — see About this demonstration.";
const EXTRACTION_INTRO =
  "Every extracted obligation below carries a verbatim quote from its primary source; claims that fail the deterministic check are rejected and counted, not hidden.";
const EXPLORE_INTRO =
  "Search, browse, and cross-reference the ingested public corpus.";
const OGC01_INTRO =
  "Neutral working analogs of the three outputs Treasury’s inventory states for OGC-01 — mapped under About this demonstration.";
const EVALUATION_INTRO =
  "Precision, recall, and F1 with confidence intervals; labels are machine-proposed and marked provisional pending human adjudication.";
const SECTION_IDS = [
  "about",
  "extraction",
  "explore",
  "ogc01",
  "evaluation",
] as const;

type SectionId = (typeof SECTION_IDS)[number];
type GroupSectionId = Exclude<SectionId, "about">;
type ForceOpenSignals = Record<GroupSectionId, number>;

interface HashNavigationRequest {
  sectionId: SectionId;
  sequence: number;
  disclosureReady: boolean;
}

const INITIAL_FORCE_OPEN_SIGNALS: ForceOpenSignals = {
  extraction: 0,
  explore: 0,
  ogc01: 0,
  evaluation: 0,
};

function isSectionId(value: string): value is SectionId {
  return SECTION_IDS.some((sectionId) => sectionId === value);
}

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
  const [exploreActive, setExploreActive] = useState(false);
  const [ogc01Active, setOgc01Active] = useState(false);
  const [evaluationActive, setEvaluationActive] = useState(false);
  const [aboutInventorySettled, setAboutInventorySettled] =
    useState(false);
  const [hashNavigationRequest, setHashNavigationRequest] =
    useState<HashNavigationRequest | null>(null);
  const [forceOpenSignals, setForceOpenSignals] =
    useState<ForceOpenSignals>(INITIAL_FORCE_OPEN_SIGNALS);
  const sourceCacheRef = useRef<Map<string, string>>(new Map());
  const hashNavigationFrameRef = useRef<number | null>(null);
  const hashNavigationSequenceRef = useRef(0);
  const selectedDocumentNumber = selectedClaim?.document_number ?? null;

  const openHashTarget = useCallback((hash: string) => {
    const sectionId = hash.startsWith("#") ? hash.slice(1) : hash;

    if (!isSectionId(sectionId)) {
      return;
    }

    hashNavigationSequenceRef.current += 1;
    setHashNavigationRequest({
      sectionId,
      sequence: hashNavigationSequenceRef.current,
      disclosureReady: sectionId === "about",
    });

    if (sectionId !== "about") {
      setForceOpenSignals((current) => ({
        ...current,
        [sectionId]: current[sectionId] + 1,
      }));
    }
  }, []);

  const markHashTargetOpen = useCallback((sectionId: GroupSectionId) => {
    setHashNavigationRequest((current) =>
      current?.sectionId === sectionId && !current.disclosureReady
        ? { ...current, disclosureReady: true }
        : current,
    );
  }, []);

  useEffect(() => {
    const aboutSection = document.querySelector(".about-section");

    if (!aboutSection) {
      setAboutInventorySettled(true);
      return;
    }

    const updateSettledState = () => {
      setAboutInventorySettled(
        aboutSection.querySelector(".about-inventory-loading") === null,
      );
    };
    const observer = new MutationObserver(updateSettledState);
    // Degrade open: a hung inventory fetch must not gate hash navigation
    // forever — after this window, scroll targets are close enough anyway.
    const settleTimeout = window.setTimeout(
      () => setAboutInventorySettled(true),
      1500,
    );

    updateSettledState();
    observer.observe(aboutSection, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      window.clearTimeout(settleTimeout);
    };
  }, []);

  useEffect(() => {
    const handleHashChange = () => openHashTarget(window.location.hash);
    const handleSameHashLinkClick = (event: MouseEvent) => {
      const eventTarget = event.target;

      if (!(eventTarget instanceof Element)) {
        return;
      }

      const anchor = eventTarget.closest("a[href]");

      if (
        !(anchor instanceof HTMLAnchorElement) ||
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey ||
        (anchor.target !== "" && anchor.target !== "_self") ||
        anchor.hasAttribute("download") ||
        anchor.origin !== window.location.origin ||
        anchor.pathname !== window.location.pathname ||
        anchor.search !== window.location.search ||
        anchor.hash !== window.location.hash ||
        !isSectionId(anchor.hash.slice(1))
      ) {
        return;
      }

      event.preventDefault();
      openHashTarget(anchor.hash);
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    document.addEventListener("click", handleSameHashLinkClick);

    return () => {
      window.removeEventListener("hashchange", handleHashChange);
      document.removeEventListener("click", handleSameHashLinkClick);
    };
  }, [openHashTarget]);

  useEffect(() => {
    if (
      !hashNavigationRequest?.disclosureReady ||
      pageData.status === "loading" ||
      (hashNavigationRequest.sectionId !== "about" &&
        !aboutInventorySettled)
    ) {
      return;
    }

    const { sectionId, sequence } = hashNavigationRequest;

    hashNavigationFrameRef.current = window.requestAnimationFrame(() => {
      hashNavigationFrameRef.current = null;
      const target = document.getElementById(sectionId);

      if (target) {
        const behavior = window.matchMedia(
          "(prefers-reduced-motion: reduce)",
        ).matches
          ? "auto"
          : "smooth";

        target.scrollIntoView({ behavior, block: "start" });
        target.focus({ preventScroll: true });
      }

      setHashNavigationRequest((current) =>
        current?.sequence === sequence ? null : current,
      );
    });

    return () => {
      if (hashNavigationFrameRef.current !== null) {
        window.cancelAnimationFrame(hashNavigationFrameRef.current);
        hashNavigationFrameRef.current = null;
      }
    };
  }, [
    aboutInventorySettled,
    hashNavigationRequest,
    pageData.status,
  ]);

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
            <p>{HERO_MOCKUP_LINE}</p>
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
      <PageNav />

      <main id="main-content" className="content-bound main-content" tabIndex={-1}>
        <AboutSection />

        <CollapsibleSection
          id="extraction"
          heading="Obligation extraction"
          defaultOpen
          onForceOpen={() => markHashTargetOpen("extraction")}
          forceOpenSignal={forceOpenSignals.extraction}
        >
          <p className="page-group-intro">{EXTRACTION_INTRO}</p>

          {pageData.status === "loading" ? (
            <div className="loading-state page-state" role="status">
              Loading the pre-computed regulatory snapshot…
            </div>
          ) : null}

          {pageData.status === "error" ? (
            <div className="error-state page-state" role="alert">
              <h3>Snapshot unavailable</h3>
              <p>
                The pre-computed data files could not be loaded.{" "}
                {pageData.message}
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
        </CollapsibleSection>

        <CollapsibleSection
          id="explore"
          heading="Explore the corpus"
          onFirstOpen={() => setExploreActive(true)}
          onForceOpen={() => markHashTargetOpen("explore")}
          forceOpenSignal={forceOpenSignals.explore}
        >
          <p className="page-group-intro">{EXPLORE_INTRO}</p>
          <SearchSection />
          <BrowseSection active={exploreActive} />
          <CrossRefSection active={exploreActive} />
        </CollapsibleSection>

        <CollapsibleSection
          id="ogc01"
          heading="OGC-01 demonstration modules"
          onFirstOpen={() => setOgc01Active(true)}
          onForceOpen={() => markHashTargetOpen("ogc01")}
          forceOpenSignal={forceOpenSignals.ogc01}
        >
          <p className="page-group-intro">{OGC01_INTRO}</p>
          <AuthoritySection active={ogc01Active} />
          <GroundingSection active={ogc01Active} />
          <DraftsSection active={ogc01Active} />
        </CollapsibleSection>

        <CollapsibleSection
          id="evaluation"
          heading="Evaluation & assurance"
          onFirstOpen={() => setEvaluationActive(true)}
          onForceOpen={() => markHashTargetOpen("evaluation")}
          forceOpenSignal={forceOpenSignals.evaluation}
        >
          <p className="page-group-intro">{EVALUATION_INTRO}</p>
          <EvalSection active={evaluationActive} />
          <Ogc01EvalSection active={evaluationActive} />
        </CollapsibleSection>
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
          <p>{FOOTER_ATTRIBUTION}</p>
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
