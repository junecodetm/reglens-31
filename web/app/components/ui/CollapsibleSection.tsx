"use client";

import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

export interface CollapsibleSectionProps {
  id: string;
  heading: ReactNode;
  headingLevel?: "h2" | "h3";
  defaultOpen?: boolean;
  onFirstOpen?: () => void;
  forceOpenSignal?: number;
  children: ReactNode;
}

export function CollapsibleSection({
  id,
  heading,
  headingLevel = "h2",
  defaultOpen = false,
  onFirstOpen,
  forceOpenSignal = 0,
  children,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const hasOpenedRef = useRef(false);
  const previousForceOpenSignalRef = useRef(0);
  const Heading = headingLevel;
  const panelId = `${id}-panel`;

  useEffect(() => {
    if (
      forceOpenSignal !== previousForceOpenSignalRef.current
    ) {
      previousForceOpenSignalRef.current = forceOpenSignal;

      if (forceOpenSignal !== 0) {
        setIsOpen(true);
      }
    }
  }, [forceOpenSignal]);

  useEffect(() => {
    if (isOpen && !hasOpenedRef.current) {
      hasOpenedRef.current = true;
      onFirstOpen?.();
    }
  }, [isOpen, onFirstOpen]);

  return (
    <section
      className="collapsible-section"
      aria-labelledby={id}
    >
      <Heading
        id={id}
        className="collapsible-section-heading"
        tabIndex={-1}
      >
        <button
          type="button"
          className="collapsible-section-button"
          aria-expanded={isOpen}
          aria-controls={panelId}
          onClick={() => setIsOpen((current) => !current)}
        >
          <span>{heading}</span>
          <span
            className="disclosure-icon"
            aria-hidden="true"
          >
            ▾
          </span>
        </button>
      </Heading>

      <div
        id={panelId}
        className="collapsible-section-panel"
        hidden={!isOpen}
      >
        {children}
      </div>
    </section>
  );
}
