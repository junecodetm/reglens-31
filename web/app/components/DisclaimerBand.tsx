import { Alert } from "@trussworks/react-uswds";

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
          Independent research prototype. Not a U.S. government website; not
          legal advice. The complete disclaimer appears in the footer of every
          page.
        </Alert>
      </div>
    </aside>
  );
}
