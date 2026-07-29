"use client";

import type { ReactNode } from "react";

import { Sidebar } from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main id="main-content" className="app-content" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
