"use client";

import { useEffect } from "react";
import { Table } from "@trussworks/react-uswds";

import type { CurrencyData, CurrencyPartData } from "./reglens-types";
import { type LazyJsonState, useLazyJson } from "./ui/useLazyJson";

const CURRENCY_PATH = "/data/currency.json";

/** Load currency.json on mount; both surfaces share the in-flight promise. */
function useCurrency(): LazyJsonState<CurrencyData> {
  const { state, load } = useLazyJson<CurrencyData>(CURRENCY_PATH, {
    fallbackErrorMessage: "The currency comparison could not be loaded.",
  });
  useEffect(() => {
    void load();
  }, [load]);
  return state;
}

/**
 * Amendment drift between the pinned corpus and the live regulation.
 *
 * The comparison runs at BUILD time against snapshotted eCFR versioner
 * responses, so the deployed page never calls a third-party origin and the
 * reported drift is reproducible from the repository alone. Both surfaces
 * render nothing until the artifact is ready — an absent file degrades to
 * silence rather than to an error.
 *
 * Framing: this records drift and takes no view on what any amendment means.
 */
export function CurrencyNote() {
  const state = useCurrency();
  if (state.status !== "ready") {
    return null;
  }
  const { total_sections, total_amended_since_snapshot, snapshot_date } =
    state.data;
  return (
    <p>
      Corpus currency: {total_amended_since_snapshot} of {total_sections}{" "}
      sections in the five ingested 31 CFR parts have been amended upstream
      since <time dateTime={snapshot_date}>{snapshot_date}</time> — recorded at
      build time from the eCFR versioner API.
    </p>
  );
}

export function CurrencySection() {
  const state = useCurrency();
  if (state.status !== "ready") {
    return null;
  }
  const currency = state.data;
  return (
    <section className="corpus-currency" aria-labelledby="corpus-currency">
      <h2 id="corpus-currency">Currency of the pinned corpus</h2>
      <p>
        This site ships a snapshot of Title 31 pinned to{" "}
        <time dateTime={currency.snapshot_date}>{currency.snapshot_date}</time>.
        At build time, each ingested part&apos;s section census is read from
        eCFR&apos;s own versioner API and compared against that date, so the
        number of sections amended upstream since then is a measured count
        rather than a disclaimer. It covers the five ingested parts only — not
        the Federal Register documents — and counts amendments without weighing
        them. Amendments are counted, not interpreted.
      </p>
      <Table bordered caption="Section census and upstream amendments per ingested 31 CFR part.">
        <thead>
          <tr>
            <th scope="col">31 CFR part</th>
            <th scope="col">Sections (eCFR census)</th>
            <th scope="col">
              Amended since{" "}
              <time dateTime={currency.snapshot_date}>
                {currency.snapshot_date}
              </time>
            </th>
          </tr>
        </thead>
        <tbody>
          {currency.parts.map((part: CurrencyPartData) => (
            <tr key={part.part}>
              <th scope="row">Part {part.part}</th>
              <td>{part.census_count}</td>
              <td>{part.amended_since_snapshot}</td>
            </tr>
          ))}
          <tr>
            <th scope="row">All parts</th>
            <td>{currency.total_sections}</td>
            <td>{currency.total_amended_since_snapshot}</td>
          </tr>
        </tbody>
      </Table>
      <p>
        The same census is what validates the section parser: the counts above
        come from eCFR, and a test asserts the parser finds exactly that many
        sections in each committed part text. The deployed page makes no network
        call — refreshing these numbers is a build step.
      </p>
    </section>
  );
}
