import type { Metadata } from "next";

import { EvalSection } from "../components/EvalSection";
import { PageHeader } from "../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Evaluation — honest, provisional — RegLens-31",
};

export default function EvaluationPage() {
  return (
    <>
      <PageHeader title="Evaluation — honest, provisional" />
      <EvalSection active />
    </>
  );
}
