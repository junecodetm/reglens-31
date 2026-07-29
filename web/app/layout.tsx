import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@trussworks/react-uswds/lib/uswds.css";
import "@trussworks/react-uswds/lib/index.css";
import "./globals.css";

import { DisclaimerBand } from "./components/DisclaimerBand";
import { AppShell } from "./components/shell/AppShell";
import { SiteFooter } from "./components/shell/SiteFooter";

export const metadata: Metadata = {
  title: "RegLens-31 — Provenance-Gated Regulatory Obligation Extraction",
  description:
    "Auditable prototype: every extracted obligation is verified verbatim against its primary source. Personal project; not affiliated with the U.S. Department of the Treasury.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        <DisclaimerBand />
        <AppShell>{children}</AppShell>
        <SiteFooter />
      </body>
    </html>
  );
}
