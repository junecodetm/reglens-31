import type { Metadata } from "next";

import { CorpusScopeInline } from "../components/CorpusScope";
import { PageHeader } from "../components/shell/PageHeader";
import { GlossaryTerm } from "../components/ui/GlossaryTerm";
import { ObligationsExplorer } from "./ObligationsExplorer";

export const metadata: Metadata = {
  title: "Extracted obligations — RegLens-31",
};

export default function ObligationsPage() {
  return (
    <>
      <PageHeader
        title="Extracted obligations"
        lead={
          <>
            Each entry is an obligation — who must do what — extracted from a
            published Treasury regulation by a local language model. A claim
            is kept only if its quoted text appears{" "}
            <GlossaryTerm term="verbatim-span">verbatim</GlossaryTerm> in the
            official source; rejected claims are counted and shown beside the
            nearest source wording.
            <CorpusScopeInline />
          </>
        }
      />
      <ObligationsExplorer standalone />
    </>
  );
}
