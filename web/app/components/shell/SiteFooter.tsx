import Link from "next/link";

import siteSnapshot from "../../../public/data/site.json";
import { CurrencyNote } from "../CurrencySection";
import {
  DISCLAIMER_TEXT,
  type SiteData,
} from "../reglens-types";

const FOOTER_ATTRIBUTION =
  "Use-case framing: Treasury AI Use Case Inventory (U.S. Government work) — see ";
// Build-time static import: site.json is committed and pinned by the
// export-replay guard, so it is always present.
const site: SiteData = siteSnapshot;

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="content-bound footer-content">
        <p>{DISCLAIMER_TEXT}</p>
        <p>
          Data as of <time dateTime={site.data_as_of}>{site.data_as_of}</time> —
          a pre-computed static snapshot; no page depends on a live service.
          Source data: Federal Register (U.S. public domain). Extraction:{" "}
          {site.model_tags.join(", ")} running locally at temperature 0.
        </p>
        <CurrencyNote />
        <p>
          {FOOTER_ATTRIBUTION}
          <Link href="/#about">About this demonstration</Link> ·{" "}
          <a href="/api/v1/index.json">Static read API (JSON)</a> ·{" "}
          <a href="https://github.com/junecodetm/reglens-31">
            Source code &amp; methodology
            <span aria-hidden="true"> ↗</span>
          </a>
        </p>
      </div>
    </footer>
  );
}
