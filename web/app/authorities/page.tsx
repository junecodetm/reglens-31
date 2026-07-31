import type { Metadata } from "next";

import { AuthoritySection } from "../components/AuthoritySection";
import { CrossRefSection } from "../components/CrossRefSection";
import { GroundingSection } from "../components/GroundingSection";
import { PageHeader } from "../components/shell/PageHeader";
import { GlossaryTerm } from "../components/ui/GlossaryTerm";
import { ViewTabs } from "../components/ui/ViewTabs";

export const metadata: Metadata = {
  title: "Statutory authority — RegLens-31",
};

export default function AuthoritiesPage() {
  return (
    <>
      <PageHeader
        title="Statutory authority"
        lead={
          <>
            Every regulation must cite the statute that authorizes it. This page
            traces each ingested part&apos;s cited authority into the U.S. Code
            and classifies each citation&apos;s language as{" "}
            <GlossaryTerm term="mandatory-discretionary-silent-unresolved">
              mandatory, discretionary, silent, or unresolved
            </GlossaryTerm>
            . It also shows which statutes several parts share and lists two
            families of textual markers found in rule preambles — presented with
            equal weight, describing the published text only.
          </>
        }
      />
      <ViewTabs
        ariaLabel="Statutory authority views"
        defaultTabId="citations"
        tabs={[
          {
            id: "citations",
            label: "Authority citations",
            panel: <AuthoritySection active standalone />,
          },
          {
            id: "shared",
            label: "Shared authorities",
            panel: <CrossRefSection active standalone />,
          },
          {
            id: "markers",
            label: "Grounding markers",
            panel: <GroundingSection active standalone />,
          },
        ]}
      />
    </>
  );
}
