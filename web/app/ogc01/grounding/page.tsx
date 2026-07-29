import type { Metadata } from "next";

import { GroundingSection } from "../../components/GroundingSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Grounding markers (two-sided) — RegLens-31",
};

export default function GroundingPage() {
  return (
    <>
      <PageHeader title="Grounding markers (two-sided)" />
      <GroundingSection active standalone />
    </>
  );
}
