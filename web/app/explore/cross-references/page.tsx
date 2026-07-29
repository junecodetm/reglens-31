import type { Metadata } from "next";

import { CrossRefSection } from "../../components/CrossRefSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Authority cross-references — RegLens-31",
};

export default function CrossReferencesPage() {
  return (
    <>
      <PageHeader title="Authority cross-references" />
      <CrossRefSection active standalone />
    </>
  );
}
