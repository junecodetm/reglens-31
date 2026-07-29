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

// This primitive owns only the container/panel wiring (stable ids, hidden
// panel, aria-labelledby); every call site supplies its own toggle markup via
// renderToggle, so the toggle is deliberately not defaulted here.
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
  renderToggle: (props: ExpandableGroupToggleProps) => ReactNode;
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

  return (
    <Container
      id={containerId ?? undefined}
      className={className ?? undefined}
      aria-labelledby={resolvedAriaLabelledby ?? undefined}
    >
      {renderToggle({
        id,
        label,
        expanded,
        onToggle,
        ariaCurrent,
        buttonId,
        panelId,
      })}
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
