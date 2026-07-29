import type { Metadata } from "next";

import { Ogc01EvalSection } from "../../components/Ogc01EvalSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title:
    "Evaluation — authority, grounding, and drafts (provisional) — RegLens-31",
};

export default function Ogc01EvaluationPage() {
  return (
    <>
      <PageHeader title="Evaluation — authority, grounding, and drafts (provisional)" />
      <Ogc01EvalSection active />
    </>
  );
}
