import type { Metadata } from "next";

import {
  CROSS_REF_INTRO,
  CrossRefSection,
} from "../../components/CrossRefSection";
import { PageHeader } from "../../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "Authority cross-references — RegLens-31",
};

export default function CrossReferencesPage() {
  return (
    <>
      <PageHeader
        title="Authority cross-references"
        lede={CROSS_REF_INTRO}
      />
      <CrossRefSection active />
    </>
  );
}
