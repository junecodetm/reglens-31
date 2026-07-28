export const DISCLAIMER_TEXT =
  "Independent personal research prototype. Not affiliated with, endorsed by, or representing the U.S. Department of the Treasury or any U.S. government agency (31 U.S.C. § 333). Outputs are assistive only — verify every obligation against the primary source.";

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
