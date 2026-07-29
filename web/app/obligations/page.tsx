import type { Metadata } from "next";

import { PageHeader } from "../components/shell/PageHeader";
import { ObligationsExplorer } from "./ObligationsExplorer";

export const metadata: Metadata = {
  title: "Extracted obligations — RegLens-31",
};

export default function ObligationsPage() {
  return (
    <>
      <PageHeader
        title="Extracted obligations"
        lead="Each entry below is an obligation — a who-must-do-what statement — that a local language model extracted from a published Treasury regulation. A claim is kept only if its quoted text appears verbatim in the official source; everything else is rejected, counted, and shown beside the nearest source wording for comparison."
      />
      <ObligationsExplorer standalone />
    </>
  );
}
