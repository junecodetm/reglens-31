import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const ROOT = new URL("../", import.meta.url);

/**
 * The deployed response headers are a security control, not a formatting
 * detail. Before this test existed the CSP was unpinned, so `connect-src`
 * could have been widened — or dropped entirely — without any check failing.
 *
 * No cross-origin connect destination is permitted at all. Corpus currency is
 * compared against eCFR at BUILD time from committed snapshots, so the deployed
 * page never calls a third-party origin (CLAUDE.md section 21); a live fetch
 * would also make the reported drift unreproducible.
 */
const EXPECTED_CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const ALLOWED_CONNECT_ORIGINS = ["'self'"];

async function headersFile() {
  return readFile(new URL("web/public/_headers", ROOT), "utf8");
}

function directive(csp, name) {
  const found = csp
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name} `));
  assert.ok(found, `CSP is missing a ${name} directive`);
  return found.slice(name.length + 1).split(/\s+/);
}

test("the Content-Security-Policy is pinned exactly", async () => {
  const headers = await headersFile();
  const line = headers
    .split("\n")
    .map((row) => row.trim())
    .find((row) => row.startsWith("Content-Security-Policy:"));

  assert.ok(line, "no Content-Security-Policy header is served");
  assert.equal(line.slice("Content-Security-Policy:".length).trim(), EXPECTED_CSP);
});

test("connect-src permits no cross-origin destination at all", async () => {
  const headers = await headersFile();
  const csp = headers.slice(headers.indexOf("Content-Security-Policy:"));

  assert.deepEqual(directive(csp, "connect-src"), ALLOWED_CONNECT_ORIGINS);
});

test("the CSP never permits a wildcard or plaintext origin", async () => {
  const headers = await headersFile();

  assert.doesNotMatch(headers, /Content-Security-Policy:[^\n]*(\*|http:\/\/)/);
});

test("hardening headers stay present", async () => {
  const headers = await headersFile();

  assert.match(headers, /^\s*X-Content-Type-Options: nosniff$/m);
  assert.match(headers, /^\s*X-Frame-Options: DENY$/m);
  assert.match(headers, /^\s*Referrer-Policy: strict-origin-when-cross-origin$/m);
  assert.match(headers, /^\s*Permissions-Policy: camera=\(\), microphone=\(\), geolocation=\(\)$/m);
});

test("the read API is served CORS-open and cacheable, and only under /api/v1/", async () => {
  const headers = await headersFile();
  const block = headers.slice(headers.indexOf("/api/v1/*"));

  assert.match(headers, /^\/api\/v1\/\*$/m);
  assert.match(block, /^\s*Access-Control-Allow-Origin: \*$/m);
  assert.match(block, /^\s*Access-Control-Allow-Methods: GET, HEAD, OPTIONS$/m);
  assert.match(block, /^\s*Cache-Control: public, max-age=\d+$/m);
  // The wildcard CORS grant must not leak onto the site itself.
  assert.doesNotMatch(headers.slice(0, headers.indexOf("/api/v1/*")), /Access-Control-Allow-Origin/);
});
