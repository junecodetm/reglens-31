import type { Metadata } from "next";

import { EvalSection } from "../components/EvalSection";
import { Ogc01EvalSection } from "../components/Ogc01EvalSection";
import { PageHeader } from "../components/shell/PageHeader";
import { GlossaryTerm } from "../components/ui/GlossaryTerm";
import { ViewTabs } from "../components/ui/ViewTabs";

export const metadata: Metadata = {
  title: "Evaluation (provisional) — RegLens-31",
};

export default function EvaluationPage() {
  return (
    <>
      <PageHeader
        title="Evaluation (provisional)"
        lead={
          <>
            Extractor accuracy, measured on a labeled sample and reported with
            confidence intervals — for obligation extraction and for the three
            modules above. Labels are machine-proposed and marked{" "}
            <GlossaryTerm term="provisional-label">provisional</GlossaryTerm>{" "}
            until human adjudication completes.
          </>
        }
      />
      <ViewTabs
        ariaLabel="Evaluation views"
        defaultTabId="core"
        tabs={[
          {
            id: "core",
            label: "Core extraction",
            panel: <EvalSection active standalone />,
          },
          {
            id: "ogc01",
            label: "Authority, grounding & drafts",
            panel: <Ogc01EvalSection active standalone />,
          },
        ]}
      />
    </>
  );
}
