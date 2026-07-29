import type { Metadata } from "next";

import { PageHeader } from "../../components/shell/PageHeader";
import { RejectedClaimsExplorer } from "./RejectedClaimsExplorer";

export const metadata: Metadata = {
  title: "Rejected claims — RegLens-31",
};

export default function RejectedClaimsPage() {
  return (
    <>
      <PageHeader title="Rejected claims" />
      <RejectedClaimsExplorer standalone />
    </>
  );
}
