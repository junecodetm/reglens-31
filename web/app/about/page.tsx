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

      <section
        className="about-governance-docs"
        aria-labelledby="about-governance-docs-heading"
      >
        <h2 id="about-governance-docs-heading">
          Methodology &amp; governance documents
        </h2>
        <p>
          The repository carries the full written record behind this
          demonstration:
        </p>
        <ul>
          <li>
            <a href="https://github.com/junecodetm/reglens-31#readme">
              README — setup, approach, tools, and assumptions
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
          <li>
            <a href="https://github.com/junecodetm/reglens-31/blob/main/docs/M25-21-CROSSWALK.md">
              OMB M-25-21 minimum-practices crosswalk (with NIST AI 600-1
              mappings)
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
          <li>
            <a href="https://github.com/junecodetm/reglens-31/tree/main/governance">
              Model card, data card, AI impact assessment, monitoring &amp;
              rollback plans
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
          <li>
            <a href="https://github.com/junecodetm/reglens-31/blob/main/docs/EVALUATION.md">
              Evaluation methodology — gold set, annotation protocol,
              intervals
              <span aria-hidden="true"> ↗</span>
            </a>
          </li>
        </ul>
      </section>
    </>
  );
}
