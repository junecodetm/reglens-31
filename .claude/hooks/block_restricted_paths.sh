#!/usr/bin/env bash
# PreToolUse hook (matcher: Write|Edit). Exit 2 = block the tool call.
# Enforces the NO-RESTRICTED-DATA INVARIANT (CLAUDE.md §2, invariant 3) and the
# no-secrets-in-code rule (docs/STANDARDS.md). Input: hook JSON on stdin.

input="$(cat)"
file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
content="$(printf '%s' "$input" | jq -r '.tool_input.content // .tool_input.new_string // empty' 2>/dev/null)"

# Restricted-data markers. Markdown files are exempt: the spec and docs must be
# able to NAME these datasets in order to exclude them — the invariant targets
# data and code, not documentation prose.
case "$file_path" in
  *.md) ;;
  *)
    if printf '%s\n%s' "$file_path" "$content" | grep -qiE 'BSA[/ _-]?SAR|suspicious activity report|beneficial ownership information|FinCEN[/ _-]?BOI|taxpayer[ _-](data|record)'; then
      echo "BLOCKED (no-restricted-data invariant): restricted-data marker in write target or content. See CLAUDE.md §2 invariant 3 and the docs/DATA_SOURCES.md exclusion list." >&2
      exit 2
    fi
    ;;
esac

# Secret-looking assignments (any file type).
if printf '%s' "$content" | grep -qiE "(api[_-]?key|secret|token|password)[[:space:]]*[:=][[:space:]]*['\"][A-Za-z0-9_/+=-]{16,}['\"]"; then
  echo "BLOCKED: possible hardcoded secret in write. Config goes via env + .env (gitignored); see docs/STANDARDS.md." >&2
  exit 2
fi
exit 0
