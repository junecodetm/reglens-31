export const DISCLAIMER_TEXT =
  "Independent personal research prototype. Not affiliated with, endorsed by, or representing the U.S. Department of the Treasury or any U.S. government agency (31 U.S.C. § 333). Not legal advice; no attorney-client relationship. Outputs are assistive only — verify every obligation against the primary source.";

export type ObligationType =
  | "requirement"
  | "prohibition"
  | "reporting"
  | "recordkeeping"
  | "disclosure"
  | "other";

export interface ExtractionRun {
  schema_version: number;
  model_tag: string;
  prompt_sha256: string;
  input_sha256: string;
  temperature: number;
}

export interface ClaimRecord {
  claim_id: string;
  document_sha256: string;
  document_number: string;
  document_title: string;
  document_url: string;
  quote: string;
  obligation_type: ObligationType;
  affected_party: string;
  summary: string;
  effective_date: string | null;
  accepted: boolean;
  start: number | null;
  end: number | null;
  rejection_reason: string | null;
  run: ExtractionRun;
}

export interface DocumentExtraction {
  document_sha256: string;
  document_number: string;
  document_title: string;
  document_url: string;
  category: string;
  accepted_count: number;
  rejected_count: number;
  claims: ClaimRecord[];
}

export interface SiteData {
  accepted_count: number;
  rejected_count: number;
  document_count: number;
  model_tags: string[];
  data_as_of: string;
}

export type SourceTextState =
  | { status: "idle" }
  | { status: "loading"; documentNumber: string }
  | { status: "ready"; documentNumber: string; text: string }
  | { status: "error"; documentNumber: string; message: string };

export type DiffOpKind = "equal" | "model" | "source";
export type DiffOp = [DiffOpKind, string];

export type RejectedDetailEntry =
  | { similarity: number; closest: null }
  | {
      similarity: number;
      closest_start: number;
      closest_end: number;
      closest_quote: string;
      diff: DiffOp[];
    };

export function hasClosestPassage(
  entry: RejectedDetailEntry,
): entry is Extract<RejectedDetailEntry, { diff: DiffOp[] }> {
  return "diff" in entry;
}

export interface RejectedDetailsData {
  schema_version: number;
  method: string;
  details: Record<string, RejectedDetailEntry>;
}

export interface ExampleClaimData {
  claim_id: string;
  document_number: string;
  document_title: string;
  summary: string;
  quote: string;
  excerpt: string;
  span_start: number;
  span_end: number;
}

export type ExampleRejectedData = {
  claim_id: string;
  document_number: string;
  document_title: string;
  summary: string;
  quote: string;
} & RejectedDetailEntry;

export interface ExampleData {
  accepted: ExampleClaimData;
  rejected: ExampleRejectedData;
}

export interface AuthorityData {
  schema_version: number;
  usc_release_point: string;
  generated_from: string;
  total_section_citations: number;
  total_resolved: number;
  total_unresolved: number;
  total_non_section_citations: number;
  gate_rejections: number;
  parts: Array<{
    part: number;
    part_heading: string;
    ecfr_date: string;
    authority_text: string;
    part_text_sha256: string;
    authority_start: number;
    authority_end: number;
    ecfr_url: string;
    citations: Array<{
      raw: string;
      kind: "usc-section" | "usc-note" | "public-law" | "executive-order";
      usc_title: number | null;
      usc_section: string | null;
      subsection: string | null;
      et_seq: boolean;
      from_range: string | null;
    }>;
    resolved: Array<{
      usc_title: number;
      usc_section: string;
      identifier: string;
      heading: string;
      status: "repealed" | "omitted" | "transferred" | null;
      text_sha256: string;
      classification:
        | "mandatory"
        | "discretionary"
        | "silent"
        | "unresolved";
      verb_quote: string | null;
      verb_start: number | null;
      verb_end: number | null;
      grant_spans: Array<{
        family: string;
        classification:
          | "mandatory"
          | "discretionary"
          | "silent"
          | "unresolved";
        quote: string;
        start: number;
        end: number;
      }>;
      gate_rejected: boolean;
      rejection_reason: string | null;
    }>;
    unresolved: Array<{
      raw: string;
      kind: "usc-section" | "usc-note" | "public-law" | "executive-order";
      usc_title: number | null;
      usc_section: string | null;
      subsection: string | null;
      et_seq: boolean;
      from_range: string | null;
    }>;
  }>;
}

export interface GroundingData {
  schema_version: number;
  band_definition: string;
  loper_bright_decided: string;
  total_gate_rejections: number;
  coverage_notes: string[];
  rules: Array<{
    document_number: string;
    title: string;
    publication_date: string;
    source_for_part: number | null;
    predates_loper_bright: boolean | null;
    cites_chevron: boolean;
    word_count: number;
    deference_count: number;
    grounding_count: number;
    deference_density_per_1k: number;
    grounding_density_per_1k: number;
    deference_band: "none" | "low" | "moderate" | "elevated";
    grounding_band: "none" | "low" | "moderate" | "elevated";
    gate_rejections: number;
    markers: Array<{
      family: string;
      side: "deference-reliance" | "grounding-strength";
      quote: string;
      start: number;
      end: number;
    }>;
  }>;
}

export interface DraftDossier {
  model: string;
  temperature: number;
  seed: number;
  num_ctx: number;
  num_predict: number;
  system_prompt_sha256: string;
  prompt_sha256: string;
  input_sha256: string;
  narrative_fields: string[];
}

export interface ConformanceData {
  generated: number;
  accepted: number;
  rejected: number;
  pass_rate: number;
  total_unverified_quotes: number;
  model_note: string;
  rejected_drafts: string[];
  checklists: Array<{
    part: number;
    doc_type: "nprm" | "final";
    headings_in_order: boolean;
    analysis_sections_present: boolean;
    placeholders_intact: boolean;
    amendatory_instructions_parse: boolean;
    amendatory_forms_demonstrated: boolean;
    authority_citation_present: boolean;
    basis_and_purpose_present: boolean;
    comment_period_reference: boolean;
    setout_text_verified: boolean;
    narrative_fabrication_clean: boolean;
    quotes_verified: boolean;
    unverified_quote_count: number;
    fabrication_hits: string[];
    dossier: DraftDossier;
    passed: boolean;
  }>;
}
