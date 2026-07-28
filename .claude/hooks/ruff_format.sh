#!/usr/bin/env bash
# PostToolUse hook (matcher: Write|Edit): auto-format Python files with ruff.
# Never blocks — always exits 0. Input: hook JSON on stdin ($CLAUDE_FILE_PATH
# no longer exists in current Claude Code; parse tool_input.file_path instead).

f="$(jq -r '.tool_input.file_path // empty' 2>/dev/null)"
case "$f" in
  *.py) ruff format "$f" >/dev/null 2>&1 || true ;;
esac
exit 0
