import type { Metadata } from "next";

import { DraftsSection } from "../components/DraftsSection";
import { PageHeader } from "../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Draft rule skeletons — RegLens-31",
};

export default function DraftsPage() {
  return (
    <>
      <PageHeader
        title="Draft rule skeletons"
        lead="A demonstration of automated rule-drafting: each entry follows the federal Document Drafting Handbook's required structure, with a fail-closed check confirming every required section is present and every quoted regulatory passage matches its source verbatim. The model writes only two narrative fields; everything else is deterministic or independently verified."
      />
      <DraftsSection active standalone />
    </>
  );
}
