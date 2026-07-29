import type { Metadata } from "next";

import { AboutSection } from "../components/AboutSection";
import { PageHeader } from "../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "About this demonstration — RegLens-31",
};

export default function AboutPage() {
  return (
    <>
      <PageHeader
        title="About this demonstration"
        lead="What OGC-01 is, why this demonstration mocks it up, and exactly which stated output each page implements — quoted verbatim from Treasury's own public record."
      />
      <AboutSection standalone />
    </>
  );
}
