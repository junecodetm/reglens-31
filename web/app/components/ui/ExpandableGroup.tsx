"use client";

import type { ReactNode } from "react";

export interface ExpandableGroupProps {
  id: string;
  label: ReactNode;
  expanded: boolean;
  onToggle: () => void;
  ariaCurrent?: boolean;
  children: ReactNode;
}

export function ExpandableGroup({
  id,
  label,
  expanded,
  onToggle,
  ariaCurrent = false,
  children,
}: ExpandableGroupProps) {
  const buttonId = `${id}-button`;
  const panelId = `${id}-panel`;

  return (
    <article
      id={id}
      className="document-group expandable-group"
      aria-labelledby={buttonId}
    >
      <h3 className="expandable-group-heading">
        <button
          id={buttonId}
          type="button"
          className="expandable-group-button"
          aria-expanded={expanded}
          aria-controls={panelId}
          aria-current={ariaCurrent ? "true" : undefined}
          onClick={onToggle}
        >
          <span>{label}</span>
          <span
            className="disclosure-icon"
            aria-hidden="true"
          >
            ▾
          </span>
        </button>
      </h3>

      <div
        id={panelId}
        className="expandable-group-panel"
        hidden={!expanded}
      >
        {children}
      </div>
    </article>
  );
}
