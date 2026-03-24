#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# TEST REMINDER — Warns when writing code files without tests
# PostToolUse hook for Write|Edit — checks if test file exists
# ═══════════════════════════════════════════════════════════════

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.file_path // .filePath // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0

# Only check code files
echo "$FILE" | grep -qE '\.(py|ts|tsx|js|jsx)$' || exit 0
# Skip if already a test file
echo "$FILE" | grep -qiE '(test_|_test\.|\.test\.|\.spec\.|conftest|__init__)' && exit 0
# Skip config/migration files
echo "$FILE" | grep -qiE '(config|settings|migration|\.d\.ts|types\.ts|index\.)' && exit 0

BASENAME=$(basename "$FILE" | sed 's/\.\(py\|ts\|tsx\|js\|jsx\)$//')
STATE_FILE="/tmp/claude_test_reminded_${BASENAME}"

# Don't nag more than once per file per session
[ -f "$STATE_FILE" ] && exit 0

# Check if any test file exists
FOUND=false
find "$(dirname "$FILE")" . -maxdepth 4 \( \
    -name "test_${BASENAME}.py" -o \
    -name "${BASENAME}_test.py" -o \
    -name "${BASENAME}.test.ts" -o \
    -name "${BASENAME}.test.tsx" -o \
    -name "${BASENAME}.test.js" -o \
    -name "${BASENAME}.spec.ts" -o \
    -name "${BASENAME}.spec.tsx" \
\) 2>/dev/null | grep -q . && FOUND=true

if [ "$FOUND" = false ]; then
    touch "$STATE_FILE"
    echo ""
    echo "⚠️  NO TESTS for $(basename "$FILE")"
    echo "   TDD required: write test_${BASENAME}.py / ${BASENAME}.test.ts BEFORE more implementation."
    echo ""
fi

exit 0
