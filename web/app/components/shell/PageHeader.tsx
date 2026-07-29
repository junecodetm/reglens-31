"use client";

import { type ReactNode, useEffect, useRef } from "react";

import { recordRouteMount } from "./route-mount-state";

interface PageHeaderProps {
  title: string;
  lead?: ReactNode;
}

export function PageHeader({ title, lead }: PageHeaderProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  const hasHandledMountRef = useRef(false);

  useEffect(() => {
    if (hasHandledMountRef.current) {
      return;
    }
    hasHandledMountRef.current = true;

    if (recordRouteMount()) {
      headingRef.current?.focus();
    }
  }, []);

  return (
    <header className="page-header">
      <h1 ref={headingRef} tabIndex={-1}>
        {title}
      </h1>
      {lead !== undefined ? <p className="page-lead">{lead}</p> : null}
    </header>
  );
}
