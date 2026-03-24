#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# COMMIT GATE — Blocks git commit if no tests exist for changed files
# PreToolUse hook for Bash — intercepts git commit commands
# ═══════════════════════════════════════════════════════════════

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
[ -z "$CMD" ] && CMD="$INPUT"

# Only intercept git commit commands
echo "$CMD" | grep -qE '^\s*git\s+commit' || exit 0

# Skip if this is a docs/chore commit (no code changes)
MSG=$(echo "$CMD" | sed -n 's/.*-m[[:space:]]*["\x27]\([^"\x27]*\)["\x27].*/\1/p')
echo "$MSG" | grep -qiE '^(docs|chore|ci|style):' && exit 0

# Get staged files
STAGED=$(git diff --cached --name-only 2>/dev/null)
[ -z "$STAGED" ] && exit 0

MISSING_TESTS=""
HAS_CODE=false

for FILE in $STAGED; do
    # Skip non-code files
    echo "$FILE" | grep -qE '\.(py|ts|tsx|js|jsx)$' || continue
    # Skip test files themselves, configs, migrations
    echo "$FILE" | grep -qiE '(test_|_test\.|\.test\.|spec\.|conftest|__init__|migration|config|settings|\.d\.ts)' && continue

    HAS_CODE=true
    BASENAME=$(basename "$FILE" | sed 's/\.\(py\|ts\|tsx\|js\|jsx\)$//')
    DIR=$(dirname "$FILE")

    # Check for corresponding test file
    FOUND_TEST=false

    # Python patterns
    if echo "$FILE" | grep -q '\.py$'; then
        for PATTERN in "test_${BASENAME}.py" "${BASENAME}_test.py" "tests/test_${BASENAME}.py" "tests/${DIR}/test_${BASENAME}.py"; do
            [ -f "$PATTERN" ] && FOUND_TEST=true && break
        done
        # Also check tests/ directory relative to project root
        find . -path "*/tests/test_${BASENAME}.py" -o -path "*/tests/**/test_${BASENAME}.py" 2>/dev/null | grep -q . && FOUND_TEST=true
    fi

    # TypeScript/JS patterns
    if echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx)$'; then
        EXT=$(echo "$FILE" | grep -oE '\.(ts|tsx|js|jsx)$')
        for PATTERN in "${DIR}/${BASENAME}.test${EXT}" "${DIR}/${BASENAME}.spec${EXT}" "${DIR}/__tests__/${BASENAME}${EXT}" "__tests__/${BASENAME}${EXT}"; do
            [ -f "$PATTERN" ] && FOUND_TEST=true && break
        done
        find . -name "${BASENAME}.test.*" -o -name "${BASENAME}.spec.*" 2>/dev/null | grep -q . && FOUND_TEST=true
    fi

    if [ "$FOUND_TEST" = false ]; then
        MISSING_TESTS="$MISSING_TESTS\n  - $FILE"
    fi
done

if [ "$HAS_CODE" = true ] && [ -n "$MISSING_TESTS" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "🚫 COMMIT BLOCKED — Missing tests for changed files:"
    echo -e "$MISSING_TESTS"
    echo ""
    echo "Write tests FIRST (TDD), then commit. No exceptions."
    echo "Skip ONLY for docs/chore: git commit -m 'docs: ...'"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
fi

exit 0
