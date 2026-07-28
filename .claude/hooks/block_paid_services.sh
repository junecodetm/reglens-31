#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash). Exit 2 = block the tool call.
# Enforces the ZERO-COST INVARIANT (CLAUDE.md §2, invariant 1): no deploy/CLI
# command that implies a card-backed billed service may run.
# Input: hook JSON on stdin; the command is tool_input.command.

cmd="$(jq -r '.tool_input.command // empty' 2>/dev/null)"
[ -z "$cmd" ] && exit 0

# Pattern is verbatim from the master spec (CLAUDE.md §19).
if printf '%s' "$cmd" | grep -qE 'flyctl|render |railway |vercel deploy|gcloud|aws |wrangler .*deploy'; then
  echo "BLOCKED (zero-cost invariant): command matches a card-implying paid-service pattern. See CLAUDE.md §2 invariant 1 and the docs/STACK.md allow-list." >&2
  exit 2
fi
exit 0
