import type { Metadata } from "next";

import {
  BROWSE_INTRO,
  BrowseSection,
} from "../../components/BrowseSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Browse Title 31 (ingested parts) — RegLens-31",
};

export default function BrowsePage() {
  return (
    <>
      <PageHeader
        title="Browse Title 31 (ingested parts)"
        lede={BROWSE_INTRO}
      />
      <BrowseSection active />
    </>
  );
}
