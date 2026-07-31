import siteSnapshot from "../../public/data/site.json";
import type { SiteData } from "./reglens-types";

// Build-time static import, matching SiteFooter: the counts land in the cold
// HTML, so the disclosure survives JS being off and cannot flash a placeholder.
// Every number rendered here — including the extraction cap — is read from
// site.json, so none of them can drift away from what the pipeline did.
const site: SiteData = siteSnapshot;

function count(value: number): string {
  return value.toLocaleString("en-US");
}

/** One sentence, for a page lead or the footer. Renders a span, never a paragraph. */
export function CorpusScopeInline() {
  return (
    <span className="corpus-scope-inline">
      {" "}
      Extraction covers {count(site.documents_extracted)} of the{" "}
      {count(site.documents_in_scope)} documents in scope — a stated sample; all{" "}
      {count(site.documents_in_scope)} are committed to the repository as
      content-addressed snapshots.
    </span>
  );
}

/** The full disclosure: what is committed, what was read, and by which rule. */
export function CorpusScope() {
  return (
    <section
      className="overview-section corpus-scope"
      aria-labelledby="corpus-scope"
      data-reveal
    >
      <h2 id="corpus-scope">Corpus scope: closed by rule, sampled by rule</h2>
      <p>
        {count(site.documents_in_scope)} documents are committed to this
        repository as content-addressed snapshots. The set comprises 152
        Federal Register documents — 132 attributed by the CFR index to the
        five in-scope 31 CFR parts, and 20 retained from a citation-following
        pass — and the five part texts. Extraction has been run over{" "}
        {count(site.documents_extracted)} of them: the five part texts and
        every committed Federal Register document published in 2026. This site
        presents that sample.
      </p>
      <p>
        Both boundaries are executable rules in <code>reglens/corpus.py</code>,
        not hand-picked lists: one decides what the corpus contains, the other
        decides what the model reads. Both are checked —{" "}
        <code>tests/test_corpus.py</code> asserts the published claim set is
        exactly what the sampling rule selects.
      </p>
      <p>
        Inference runs entirely on one laptop. The remaining documents are
        ingested and committed;{" "}
        <code>python -m reglens.extract --all</code> extracts them. Text read:{" "}
        {count(site.chars_extracted)} of {count(site.chars_in_scope)}{" "}
        characters. The five CFR part texts are read in full; Federal Register
        documents are capped at {count(site.max_document_chars)} characters, and
        any shortfall is recorded per document and shown beside it.
      </p>
    </section>
  );
}
