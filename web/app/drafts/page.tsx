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
        lead="Each draft follows the structure required by the federal Document Drafting Handbook, verified by a fail-closed conformance check. The model writes only two labeled narrative fields; every other section is deterministic template output, and every quoted regulatory passage must match its source verbatim."
      />
      <DraftsSection active standalone />
    </>
  );
}
