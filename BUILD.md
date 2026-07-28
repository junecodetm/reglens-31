# RegLens-31 — Single-Pass Build to Done

Read CLAUDE.md first. It is the spec. This prompt governs HOW you execute it today.

## 0. PREFLIGHT — do this before anything else, in ONE message

Ask me for everything you will need for the entire run, as a single numbered list.
Then STOP and wait. After I answer, you run unattended to completion. Do not ask me
anything again unless a hard blocker makes progress impossible.

Determine the full list yourself, but it must include at minimum:
- GitHub repo name + whether it already exists
- Confirmation Ollama is installed and which model is pulled (recommend one for my
  RAM; if none pulled, give me the exact `ollama pull` command and wait)
- Cloudflare Pages: account connected? If not, give me the exact steps and wait
- Playwright MCP: confirm available; if not, exact install command and wait
- Any decision where guessing wrong would cost >30 min of rework

Verify each answer programmatically before proceeding (`ollama list`, `gh auth status`,
etc.). Do not trust my answers — check.

## 1. OPERATING RULES — non-negotiable

CONTEXT DISCIPLINE. Your context is the scarcest resource. Protect it:
- NEVER read a file you just wrote. You know what is in it.
- NEVER cat, print, or echo file contents to show me your work.
- Use targeted `rg` with line ranges instead of reading whole files.
- Delegate anything producing >100 lines of output to a subagent. Subagents return
  ONLY a verdict and a diff-sized findings list — never raw content.
- Run long commands with output piped to a file, then grep the file.
- Do not summarize your progress unless something failed. Silence = working.
- If context exceeds ~60%, immediately checkpoint state to docs/PROGRESS.md and
  compact. Never let context bloat force a mid-task compaction.

TOKEN DISCIPLINE:
- Write files once, correctly. No exploratory drafts.
- Batch related edits into a single tool call.
- Prefer `just` recipes over long inline shell.
- No commentary in code beyond docstrings and fail-closed markers.

SUBAGENT POLICY. Spawn fresh, context-free subagents for all review and bulk work.
Each gets a narrow brief and returns a verdict + findings only:
- `gold-annotator` — proposes gold-set spans/labels (see §4)
- `security-reviewer` — supply chain, secrets, injection, least-privilege
- `eval-auditor` — Wilson formula, bootstrap, kappa correctness
- `code-reviewer` — senior-level code quality, dead code, type gaps
- `a11y-auditor` — WCAG 2.1 AA violations
Run independent subagents in parallel. Never let a subagent write to main context.

## 2. DEFINITION OF DONE — all must be true before you stop

1. Public GitHub repo, clean commit history, Conventional Commits, CI green.
2. Live Cloudflare Pages URL that loads cold with no API key and no backend.
3. `just demo` runs fully offline on a clean clone.
4. Provenance gate rejects a fabricated quote — proven by a passing test AND a
   visible rejection counter in the UI.
5. Eval page renders P/R/F1 with 95% Wilson CIs and Cohen's kappa, honestly labeled.
6. README covers approach, tools, assumptions, limitations, non-affiliation
   disclaimer (31 U.S.C. §333), and the zero-friction demo path.
7. Zero-cost invariant holds — no card, no paid service, anywhere.
8. Playwright audit passes (§5).
9. docs/PROGRESS.md says "COMPLETE — no remaining work."

## 3. BUILD ORDER — vertical slice first, always shippable

Commit and push after each step. Never leave the repo broken.

1. Scaffold: uv, ruff, pyright strict, pytest, justfile, .gitignore, LICENSE
   (Apache-2.0), CI workflow. Push. CI must be green before step 2.
2. Ingest ONE Federal Register document → content-addressed snapshot under
   data/raw/<sha256>/ with manifest.json.
3. Extraction: pydantic v2 schema, Ollama with JSON-schema constraint, temp 0,
   pinned model tag recorded.
4. Provenance gate: normalize (unicode NFKC, whitespace), exact substring check,
   fail-closed. Property-test with hypothesis. THIS IS THE HEART — write it first-class.
5. Static UI: obligation list → click → source panel with the span highlighted →
   rejection counter in the header. Semantic HTML, keyboard operable.
6. Deploy to Cloudflare Pages. **You now have a live URL. Everything after this is
   upside, not risk.**
7. Scale ingest to ~30 documents across Federal Register + eCFR Title 31.
8. Gold set + eval (§4).
9. Security suite, SBOM, docs, governance stubs.

If you fall behind, de-scope in this order: OFAC ownership graph → OSCAL → SLSA →
Groq escalation path. Never de-scope: the gate, the eval, the disclaimer, a11y basics.

## 4. GOLD SET — honest labeling protocol

Subagents PROPOSE labels. They do not create ground truth.

- `gold-annotator` subagents (run several in parallel, each on a disjoint batch)
  propose {span, label, affected_party, effective_date} for ≥150 provisions.
- Every record carries `adjudicated: false` and `proposed_by: <model>`.
- Build docs/ADJUDICATE.md: a numbered worklist I can review at ~20/evening, with
  the provision text, the proposed label, and accept/reject/edit fields.
- The eval MUST report metrics against the machine-proposed set and label them
  exactly as: "Provisional — machine-proposed labels, human-adjudicated: 0/150.
  Metrics will be restated as adjudication proceeds."
- Never write, print, or imply "hand-labeled" anywhere until adjudication is done.
- Wire the adjudicated count so it updates automatically from the JSONL.

This is deliberate: a false provenance claim on an evaluation would be
disqualifying for this role. Provisional-and-honest is strictly stronger.

## 5. PLAYWRIGHT AUDIT LOOP — run until clean, then once more

Serve the built static site on localhost. Drive it with Playwright MCP. Loop:
fix → rebuild → re-audit. Do not stop at "mostly works."

Assert:
- Page loads <2s cold, no console errors, no failed network requests
- Clicking an obligation highlights the correct span in the source panel
- Rejection counter is present and non-zero
- Full keyboard traversal: tab order sane, focus always visible, no traps
- Screenshots at 1440px, 768px, 375px — no overflow, no clipped text
- Every link resolves (no 404s, no localhost URLs in the deployed build)
- Disclaimer visible without scrolling on the landing view
- axe-core: zero serious/critical violations
- Deployed Cloudflare URL passes the same suite as localhost

Exit criterion: two consecutive fully clean passes with no fixes between them.

## 6. QUALITY BAR — senior, not student

- pyright strict, zero errors, zero ignores. ruff clean.
- Full type annotations. Pydantic models at every boundary. No untyped dicts crossing
  module lines.
- Pure functions for the gate and metrics; side effects isolated in ingest/ and store/.
- Every fail-closed path explicitly commented as such.
- Tests: unit for the gate, hypothesis for the normalizer, cassettes for HTTP.
  No network in tests.
- No dead code, no TODOs, no commented-out blocks, no unused deps at completion.
- Deterministic: temp 0, pinned model, recorded input SHA, reproducible runs.

## 7. FINISH

When §2 is fully satisfied:
- Run all subagent reviewers one final time in parallel. Fix everything they find.
- Write docs/PROGRESS.md: what was built, what was de-scoped and why, the
  adjudication worklist status, and the exact next actions for me.
- Report in under 200 words: live URL, repo URL, eval numbers with CIs and their
  provisional label, what was de-scoped, and anything that needs my judgment.

Begin with §0. Ask everything at once, then run to completion.