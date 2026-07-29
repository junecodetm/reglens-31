import type { Metadata } from "next";

import { AboutSection } from "../components/AboutSection";
import { PageHeader } from "../components/shell/PageHeader";

export const metadata: Metadata = {
  title: "About this demonstration — RegLens-31",
};

export default function AboutPage() {
  return (
    <>
      <PageHeader title="About this demonstration" />
      <AboutSection />
    </>
  );
}
