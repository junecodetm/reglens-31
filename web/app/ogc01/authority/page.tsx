import type { Metadata } from "next";

import { AuthoritySection } from "../../components/AuthoritySection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Statutory authority — RegLens-31",
};

export default function AuthorityPage() {
  return (
    <>
      <PageHeader title="Statutory authority" />
      <AuthoritySection active standalone />
    </>
  );
}
