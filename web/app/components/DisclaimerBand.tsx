import { Alert } from "@trussworks/react-uswds";

import { DISCLAIMER_TEXT } from "./reglens-types";

export function DisclaimerBand() {
  return (
    <aside className="disclaimer-band" aria-label="Important disclaimer">
      <div className="content-bound">
        <Alert
          type="warning"
          headingLevel="h2"
          slim
          className="disclaimer-alert"
        >
          {DISCLAIMER_TEXT}
        </Alert>
      </div>
    </aside>
  );
}
