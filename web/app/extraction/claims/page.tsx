import type { Metadata } from "next";

import { PageHeader } from "../../components/shell/PageHeader";
import { ClaimsExplorer } from "./ClaimsExplorer";

export const metadata: Metadata = {
  title: "Extracted obligations — RegLens-31",
};

export default function ClaimsPage() {
  return (
    <>
      <PageHeader title="Extracted obligations" />
      <ClaimsExplorer standalone />
    </>
  );
}
