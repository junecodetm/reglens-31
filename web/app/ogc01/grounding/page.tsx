import type { Metadata } from "next";

import { GroundingSection } from "../../components/GroundingSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Statutory grounding signal (two-sided) — RegLens-31",
};

export default function GroundingPage() {
  return (
    <>
      <PageHeader title="Statutory grounding signal (two-sided)" />
      <GroundingSection active />
    </>
  );
}
