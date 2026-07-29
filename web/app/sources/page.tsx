import type { Metadata } from "next";

import { BrowseSection } from "../components/BrowseSection";
import { PageHeader } from "../components/shell/PageHeader";
import { SearchSection } from "../components/SearchSection";
import { ViewTabs } from "../components/ui/ViewTabs";

export const metadata: Metadata = {
  title: "Search & browse the corpus — RegLens-31",
};

export default function SourcesPage() {
  return (
    <>
      <PageHeader
        title="Search & browse the corpus"
        lead="Two utilities over the ingested corpus: full-text search across extracted claims, U.S. Code sections, CFR sections, and draft skeletons; and a part-by-section browser for the five ingested parts of Title 31."
      />
      <ViewTabs
        ariaLabel="Corpus views"
        defaultTabId="search"
        tabs={[
          {
            id: "search",
            label: "Search",
            panel: <SearchSection standalone />,
          },
          {
            id: "browse",
            label: "Browse Title 31",
            panel: <BrowseSection active standalone />,
          },
        ]}
      />
    </>
  );
}
