import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const ROOT = new URL("../", import.meta.url);

test("use-case-inventory.json carries pinned provenance and the verbatim OGC-01 row", async () => {
  const payload = JSON.parse(
    await readFile(new URL("web/public/data/use-case-inventory.json", ROOT), "utf8"),
  );

  assert.equal(payload.schema_version, 1);
  assert.equal(
    payload.source_url,
    "https://home.treasury.gov/system/files/136/Treasury-AI-Use-Case-Inventory.csv",
  );
  assert.match(payload.fetched_at, /^\d{4}-\d{2}-\d{2}T/);
  // Exact pinned digest — a re-snapshot must update this deliberately, in
  // lockstep with INVENTORY_SNAPSHOT_SHA256 in reglens/store/export_web.py.
  assert.equal(
    payload.sha256,
    "8e3f3332f26af5de23c2c0dda4c8e41f0ceb9097edcbd169e1216e0e6cf7512f",
  );

  assert.equal(payload.row["Use Case ID"], "OGC-01");
  assert.equal(payload.row["Use Case Name"], "Regulatory Reform Tool");
  assert.equal(payload.row["Bureau/Component"], "General Counsel");
  assert.equal(payload.row["AI Classification"], "Generative AI");
  assert.equal(payload.row["Is the AI use case high-impact?"], "High-impact");
  // The source file's own typo is preserved verbatim; the UI flags it [sic].
  assert.match(payload.row["Describe the AI system’s outputs."], /Looper Bright/);

  assert.equal(payload.context.total_use_cases, 129);
  assert.deepEqual(payload.context.general_counsel_use_case_ids, ["OGC-01"]);
  assert.equal(payload.context.high_impact.length, 4);
  const highImpactIds = payload.context.high_impact.map((entry) => entry.use_case_id);
  assert.ok(highImpactIds.includes("OGC-01"));
});
