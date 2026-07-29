"use client";

import { type ReactNode, useState } from "react";

import { lookupGlossaryTerm } from "./glossary";

interface GlossaryTermProps {
  term: string;
  children: ReactNode;
}

export function GlossaryTerm({ term, children }: GlossaryTermProps) {
  const [open, setOpen] = useState(false);
  const definition = lookupGlossaryTerm(term);

  if (definition === null) {
    return <>{children}</>;
  }

  return (
    <>
      <button
        type="button"
        className="glossary-term"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {children}
      </button>
      <span
        role="note"
        className="glossary-definition"
        hidden={!open}
      >
        {definition}
      </span>
    </>
  );
}
