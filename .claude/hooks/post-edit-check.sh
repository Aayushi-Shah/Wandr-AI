#!/bin/bash
# PostToolUse hook — runs after every Write/Edit tool call.
# Lints the changed file immediately so errors surface inline.
# Silent on clean files (no output = no noise).
#
# Requires in PATH: ruff (Python), pnpm (TypeScript)
# TOOL_INPUT env var: JSON with file_path key (set by Claude Code)

FILE=$(echo "${TOOL_INPUT}" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)

if [[ -z "$FILE" ]]; then exit 0; fi

# Python files → ruff (fast, catches E/F/W/I errors)
if [[ "$FILE" == *.py ]]; then
  RESULT=$(ruff check "$FILE" 2>&1)
  if [[ -n "$RESULT" ]]; then
    echo "=== ruff: $FILE ==="
    echo "$RESULT"
  fi
  exit 0
fi

# TypeScript / TSX → tsc --noEmit (project-wide for cross-file type errors)
if [[ "$FILE" == *.ts || "$FILE" == *.tsx ]]; then
  if [[ "$FILE" == */frontend/* ]]; then
    RESULT=$(cd /Users/aayushi/Projects/wandr-ai && pnpm --filter @wandr/frontend exec tsc --noEmit 2>&1 | head -30)
    if [[ -n "$RESULT" ]]; then
      echo "=== tsc: frontend ==="
      echo "$RESULT"
    fi
  elif [[ "$FILE" == */shared/* ]]; then
    RESULT=$(cd /Users/aayushi/Projects/wandr-ai && pnpm --filter @wandr/shared exec tsc --noEmit 2>&1 | head -30)
    if [[ -n "$RESULT" ]]; then
      echo "=== tsc: shared ==="
      echo "$RESULT"
    fi
  fi
  exit 0
fi

exit 0
