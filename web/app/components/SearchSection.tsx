"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Button } from "@trussworks/react-uswds";

import {
  encodePathSegments,
  rankSearchUnits,
  type RankedSearchResult,
  type SearchIndexData,
  type SearchUnit,
} from "./search-utils";

type SearchIndexState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: SearchIndexData }
  | { status: "error"; message: string };

type ResultTextState =
  | { status: "loading" }
  | { status: "ready"; text: string }
  | { status: "error"; message: string };

const SEARCH_INTRO =
  "Lexical search over extracted obligations, U.S. Code sections, CFR part sections, and draft skeletons. Exact-term matching against a precomputed index — no semantic ranking, no external service, and no model involvement.";

const TYPE_LABELS: Record<SearchUnit["type"], string> = {
  claim: "Extracted claim",
  usc: "U.S. Code section",
  "cfr-section": "CFR section",
  draft: "Draft skeleton",
};

async function fetchText(path: string, signal: AbortSignal): Promise<string> {
  const response = await fetch(path, { signal });

  if (!response.ok) {
    throw new Error(`The text request returned status ${response.status}.`);
  }

  return response.text();
}

function claimText(unit: Extract<SearchUnit, { type: "claim" }>): string {
  return `${unit.label}\n\nFrom document ${unit.ref}`;
}

export function SearchSection() {
  const [query, setQuery] = useState("");
  const [indexState, setIndexState] = useState<SearchIndexState>({
    status: "idle",
  });
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<RankedSearchResult[]>([]);
  const [expandedResults, setExpandedResults] = useState<Set<number>>(
    () => new Set(),
  );
  const [resultTextStates, setResultTextStates] = useState<
    Record<number, ResultTextState>
  >({});

  const indexRequestedRef = useRef(false);
  const indexControllerRef = useRef<AbortController | null>(null);
  const resultRequestsRef = useRef<Set<number>>(new Set());
  const resultControllersRef = useRef<Map<number, AbortController>>(
    new Map(),
  );

  useEffect(() => {
    return () => {
      indexControllerRef.current?.abort();
      resultControllersRef.current.forEach((controller) => controller.abort());
    };
  }, []);

  async function loadIndex(): Promise<SearchIndexData | null> {
    if (indexState.status === "ready") {
      return indexState.data;
    }

    if (indexRequestedRef.current) {
      return null;
    }

    indexRequestedRef.current = true;
    const controller = new AbortController();
    indexControllerRef.current = controller;
    setIndexState({ status: "loading" });

    try {
      const response = await fetch("/data/search-index.json", {
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(
          `The search-index request returned status ${response.status}.`,
        );
      }

      const data = (await response.json()) as SearchIndexData;

      if (!controller.signal.aborted) {
        setIndexState({ status: "ready", data });
        return data;
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        indexRequestedRef.current = false;
        setIndexState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "The search index could not be loaded.",
        });
      }
    } finally {
      if (indexControllerRef.current === controller) {
        indexControllerRef.current = null;
      }
    }

    return null;
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const index =
      indexState.status === "ready" ? indexState.data : await loadIndex();

    if (!index) {
      return;
    }

    setResults(rankSearchUnits(index, query));
    setExpandedResults(new Set());
    setHasSearched(true);
  }

  async function loadResultText(result: RankedSearchResult) {
    const { unit, unitIndex } = result;
    const resultTextState = resultTextStates[unitIndex];

    if (
      (resultTextState !== undefined && resultTextState.status !== "error") ||
      resultRequestsRef.current.has(unitIndex)
    ) {
      return;
    }

    if (unit.type === "claim") {
      setResultTextStates((current) => ({
        ...current,
        [unitIndex]: { status: "ready", text: claimText(unit) },
      }));
      return;
    }

    const controller = new AbortController();
    resultRequestsRef.current.add(unitIndex);
    resultControllersRef.current.set(unitIndex, controller);
    setResultTextStates((current) => ({
      ...current,
      [unitIndex]: { status: "loading" },
    }));

    try {
      let text: string;

      if (unit.type === "usc") {
        text = await fetchText(
          `/data/${encodePathSegments(unit.ref)}`,
          controller.signal,
        );
      } else if (unit.type === "cfr-section") {
        const partText = await fetchText(
          `/data/authority-parts/31-CFR-${encodeURIComponent(String(unit.ref.part))}.txt`,
          controller.signal,
        );
        const sectionText = partText.slice(unit.ref.start, unit.ref.end);

        if (
          unit.ref.end > partText.length ||
          unit.ref.start >= unit.ref.end ||
          !sectionText.startsWith("§")
        ) {
          throw new Error(
            "Section offsets do not match the served part text.",
          );
        }

        text = sectionText;
      } else {
        text = await fetchText(
          `/data/drafts/${encodeURIComponent(unit.ref)}`,
          controller.signal,
        );
      }

      if (!controller.signal.aborted) {
        setResultTextStates((current) => ({
          ...current,
          [unitIndex]: { status: "ready", text },
        }));
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setResultTextStates((current) => ({
          ...current,
          [unitIndex]: {
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "The result text could not be loaded.",
          },
        }));
      }
    } finally {
      resultRequestsRef.current.delete(unitIndex);
      resultControllersRef.current.delete(unitIndex);
    }
  }

  function toggleResult(result: RankedSearchResult) {
    const willExpand = !expandedResults.has(result.unitIndex);

    setExpandedResults((current) => {
      const next = new Set(current);

      if (next.has(result.unitIndex)) {
        next.delete(result.unitIndex);
      } else {
        next.add(result.unitIndex);
      }

      return next;
    });

    if (willExpand) {
      void loadResultText(result);
    }
  }

  return (
    <section
      className="eval-section search-section"
      aria-labelledby="search-heading"
    >
      <h2 id="search-heading">Search the ingested corpus</h2>
      <p>{SEARCH_INTRO}</p>

      <form className="search-form" onSubmit={(event) => void handleSearch(event)}>
        <label htmlFor="corpus-search-input">Search terms</label>
        <div className="search-form-controls">
          <input
            className="usa-input"
            id="corpus-search-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Button
            type="submit"
            base
            outline
            disabled={indexState.status === "loading"}
          >
            Search
          </Button>
        </div>
      </form>

      {indexState.status === "loading" ? (
        <p role="status">Loading the search index…</p>
      ) : null}

      {indexState.status === "error" ? (
        <div className="neutral-notice" role="alert">
          <p>
            <strong>Search index unavailable.</strong> {indexState.message}
          </p>
        </div>
      ) : null}

      {indexState.status === "ready" && hasSearched ? (
        results.length === 0 ? (
          <p>No matches in the ingested corpus for that query.</p>
        ) : (
          <ol className="search-results" aria-label="Corpus search results">
            {results.map((result) => {
              const { unit, unitIndex } = result;
              const panelId = `search-result-${unitIndex}-panel`;
              const isExpanded = expandedResults.has(unitIndex);
              const textState = resultTextStates[unitIndex];

              return (
                <li className="search-result" key={unit.id}>
                  <Button
                    type="button"
                    base
                    outline
                    className="width-full text-left"
                    aria-expanded={isExpanded}
                    aria-controls={panelId}
                    onClick={() => toggleResult(result)}
                  >
                    <span className="search-result-heading">
                      <span className="search-type-badge">
                        {TYPE_LABELS[unit.type]}
                      </span>
                      <span className="text-bold">{unit.label}</span>
                    </span>
                    <span className="search-result-snippet">
                      {unit.snippet}
                    </span>
                  </Button>

                  <div id={panelId} hidden={!isExpanded}>
                    {textState?.status === "loading" ? (
                      <p role="status">Loading full text for {unit.label}…</p>
                    ) : null}

                    {textState?.status === "error" ? (
                      <div className="neutral-notice" role="alert">
                        <p>
                          <strong>Result text unavailable.</strong>{" "}
                          {textState.message}
                        </p>
                      </div>
                    ) : null}

                    {textState?.status === "ready" ? (
                      <pre
                        className="source-document"
                        tabIndex={0}
                        role="region"
                        aria-label={`Full text for ${unit.label}`}
                      >
                        {textState.text}
                      </pre>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ol>
        )
      ) : null}
    </section>
  );
}
