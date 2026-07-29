import type { Metadata } from "next";

import { SearchSection } from "../../components/SearchSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Search the ingested corpus — RegLens-31",
};

export default function SearchPage() {
  return (
    <>
      <PageHeader title="Search the ingested corpus" />
      <SearchSection standalone />
    </>
  );
}
