import type { Metadata } from "next";

import { DraftsSection } from "../../components/DraftsSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Draft rule skeletons — RegLens-31",
};

export default function DraftsPage() {
  return (
    <>
      <PageHeader title="Draft rule skeletons" />
      <DraftsSection active standalone />
    </>
  );
}
