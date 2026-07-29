"use client";

import type { ReactNode } from "react";

export interface ExpandableGroupToggleProps {
  id: string;
  label: ReactNode;
  expanded: boolean;
  onToggle: () => void;
  ariaCurrent: boolean;
  buttonId: string;
  panelId: string;
}

export interface ExpandableGroupProps {
  id: string;
  label: ReactNode;
  expanded: boolean;
  onToggle: () => void;
  ariaCurrent?: boolean;
  as?: "article" | "li";
  containerId?: string | null;
  className?: string | null;
  ariaLabelledby?: string | null;
  panelId?: string;
  panelClassName?: string | null;
  renderToggle?: (props: ExpandableGroupToggleProps) => ReactNode;
  beforePanel?: ReactNode;
  afterPanel?: ReactNode;
  children: ReactNode;
}

export function ExpandableGroup({
  id,
  label,
  expanded,
  onToggle,
  ariaCurrent = false,
  as: Container = "article",
  containerId = id,
  className = "document-group expandable-group",
  ariaLabelledby,
  panelId: providedPanelId,
  panelClassName = "expandable-group-panel",
  renderToggle,
  beforePanel,
  afterPanel,
  children,
}: ExpandableGroupProps) {
  const buttonId = `${id}-button`;
  const panelId = providedPanelId ?? `${id}-panel`;
  const resolvedAriaLabelledby =
    ariaLabelledby === undefined ? buttonId : ariaLabelledby;
  const toggleProps: ExpandableGroupToggleProps = {
    id,
    label,
    expanded,
    onToggle,
    ariaCurrent,
    buttonId,
    panelId,
  };
  const toggle = renderToggle ? (
    renderToggle(toggleProps)
  ) : (
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
  );

  return (
    <Container
      id={containerId ?? undefined}
      className={className ?? undefined}
      aria-labelledby={resolvedAriaLabelledby ?? undefined}
    >
      {toggle}
      {beforePanel}

      <div
        id={panelId}
        className={panelClassName ?? undefined}
        hidden={!expanded}
      >
        {children}
      </div>
      {afterPanel}
    </Container>
  );
}
