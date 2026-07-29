import type { Metadata } from "next";

import { BrowseSection } from "../../components/BrowseSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Browse Title 31 (ingested parts) — RegLens-31",
};

export default function BrowsePage() {
  return (
    <>
      <PageHeader title="Browse Title 31 (ingested parts)" />
      <BrowseSection active standalone />
    </>
  );
}
