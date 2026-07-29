"use client";

import { useEffect, useId, useRef } from "react";

export interface HighlightSegments {
  before: string;
  highlighted: string;
  after: string;
}

export type HighlightSegmentsResult =
  | { status: "ready"; segments: HighlightSegments }
  | { status: "missing-offsets"; segments: null }
  | { status: "invalid-bounds"; segments: null };

export interface HighlightedTextProps {
  text: string;
  start: number | null;
  end: number | null;
  selectionKey: string;
  regionLabel: string;
  highlightStatus: string;
  noSpanMessage: string;
  boundsMessage: string;
  contextChars?: number;
  scroll?: "center" | "nearest";
  scrollBehavior?: "auto" | "smooth";
  retryWhenVisible?: boolean;
  as?: "div" | "pre";
  showStatus?: boolean;
  descriptionId?: string;
  readyStatusClassName?: string;
  noticeStatusClassName?: string;
}

export function computeHighlightSegments(
  text: string,
  start: number | null,
  end: number | null,
  contextChars?: number,
): HighlightSegmentsResult {
  if (
    contextChars !== undefined &&
    (!Number.isInteger(contextChars) || contextChars < 0)
  ) {
    throw new RangeError(
      "contextChars must be a non-negative integer when provided.",
    );
  }

  if (start === null && end === null) {
    return { status: "missing-offsets", segments: null };
  }

  if (
    start === null ||
    end === null ||
    !Number.isInteger(start) ||
    !Number.isInteger(end) ||
    start < 0 ||
    end <= start ||
    end > text.length
  ) {
    return { status: "invalid-bounds", segments: null };
  }

  const windowStart =
    contextChars === undefined ? 0 : Math.max(0, start - contextChars);
  const windowEnd =
    contextChars === undefined
      ? text.length
      : Math.min(text.length, end + contextChars);

  return {
    status: "ready",
    segments: {
      before: text.slice(windowStart, start),
      highlighted: text.slice(start, end),
      after: text.slice(end, windowEnd),
    },
  };
}

function encodeIdSegment(value: string): string {
  const encoded = Array.from(value, (character) =>
    character.codePointAt(0)!.toString(16),
  ).join("-");

  return encoded || "empty";
}

function scrollHighlight(
  panel: HTMLElement,
  highlight: HTMLElement,
  position: "center" | "nearest",
  scrollBehavior: "auto" | "smooth",
): boolean {
  if (panel.offsetParent === null || highlight.offsetParent === null) {
    return false;
  }

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const behavior =
    scrollBehavior === "auto" || prefersReducedMotion
      ? "auto"
      : "smooth";

  if (position === "nearest") {
    highlight.scrollIntoView({
      behavior,
      block: "nearest",
      inline: "nearest",
    });
    return true;
  }

  const panelRect = panel.getBoundingClientRect();
  const highlightRect = highlight.getBoundingClientRect();
  const targetTop =
    panel.scrollTop +
    (highlightRect.top - panelRect.top) -
    (panel.clientHeight - highlightRect.height) / 2;

  panel.scrollTo({
    top: Math.max(0, targetTop),
    behavior,
  });
  return true;
}

export function HighlightedText({
  text,
  start,
  end,
  selectionKey,
  regionLabel,
  highlightStatus,
  noSpanMessage,
  boundsMessage,
  contextChars,
  scroll = "center",
  scrollBehavior = "smooth",
  retryWhenVisible = true,
  as = "div",
  showStatus = true,
  descriptionId: providedDescriptionId,
  readyStatusClassName = "screen-reader-only",
  noticeStatusClassName = "neutral-notice margin-top-1",
}: HighlightedTextProps) {
  const panelRef = useRef<HTMLElement | null>(null);
  const markRef = useRef<HTMLElement>(null);
  const instanceId = useId();
  const result = computeHighlightSegments(
    text,
    start,
    end,
    contextChars,
  );
  const descriptionId =
    providedDescriptionId ??
    [
      "highlighted-text-status",
      encodeIdSegment(selectionKey),
      encodeIdSegment(instanceId),
    ].join("-");

  useEffect(() => {
    const panel = panelRef.current;
    const highlight = markRef.current;

    if (!panel || !highlight) {
      return;
    }

    if (
      scrollHighlight(
        panel,
        highlight,
        scroll,
        scrollBehavior,
      )
    ) {
      return;
    }

    if (!retryWhenVisible) {
      return;
    }

    let mutationObserver: MutationObserver | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let pending = true;

    const stopObserving = () => {
      mutationObserver?.disconnect();
      resizeObserver?.disconnect();
    };
    const retryScrollWhenVisible = () => {
      if (
        pending &&
        scrollHighlight(
          panel,
          highlight,
          scroll,
          scrollBehavior,
        )
      ) {
        pending = false;
        stopObserving();
      }
    };

    // A highlight can finish rendering below a hidden disclosure panel.
    // Keep the scroll pending until layout visibility returns, then disconnect.
    mutationObserver = new MutationObserver(retryScrollWhenVisible);

    for (
      let ancestor: HTMLElement | null = panel;
      ancestor !== null;
      ancestor = ancestor.parentElement
    ) {
      mutationObserver.observe(ancestor, {
        attributes: true,
        attributeFilter: ["class", "hidden", "style"],
      });
    }

    if (typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(retryScrollWhenVisible);
      resizeObserver.observe(panel);
    }

    return () => {
      pending = false;
      stopObserving();
    };
  }, [
    contextChars,
    end,
    retryWhenVisible,
    scroll,
    scrollBehavior,
    selectionKey,
    start,
    text,
  ]);

  const documentChildren =
    result.status === "ready" ? (
      <>
        {result.segments.before}
        <mark ref={markRef}>{result.segments.highlighted}</mark>
        {result.segments.after}
      </>
    ) : (
      text
    );
  const setPanelRef = (element: HTMLElement | null) => {
    panelRef.current = element;
  };

  return (
    <>
      {showStatus ? (
        <p
          id={descriptionId}
          className={
            result.status === "ready"
              ? readyStatusClassName
              : noticeStatusClassName
          }
          role="status"
        >
          {result.status === "ready"
            ? highlightStatus
            : result.status === "missing-offsets"
              ? noSpanMessage
              : boundsMessage}
        </p>
      ) : null}

      {as === "pre" ? (
        <pre
          ref={setPanelRef}
          className="source-document"
          tabIndex={0}
          role="region"
          aria-label={regionLabel}
          aria-describedby={showStatus ? descriptionId : undefined}
        >
          {documentChildren}
        </pre>
      ) : (
        <div
          ref={setPanelRef}
          className="source-document"
          tabIndex={0}
          role="region"
          aria-label={regionLabel}
          aria-describedby={showStatus ? descriptionId : undefined}
        >
          {documentChildren}
        </div>
      )}
    </>
  );
}
