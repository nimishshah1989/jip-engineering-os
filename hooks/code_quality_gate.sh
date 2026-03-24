#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# CODE QUALITY GATE — Checks file size, complexity, patterns
# PostToolUse hook for Write|Edit — runs after every code change
# ═══════════════════════════════════════════════════════════════

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.file_path // .filePath // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

# Only check code files
echo "$FILE" | grep -qE '\.(py|ts|tsx|js|jsx)$' || exit 0

WARNINGS=""

# Check file length (400 line limit per CLAUDE.md)
LINES=$(wc -l < "$FILE" 2>/dev/null | tr -d ' ')
if [ "$LINES" -gt 400 ]; then
    WARNINGS="$WARNINGS\n  🚫 FILE TOO LONG: $(basename $FILE) is $LINES lines (limit: 400). Split it."
elif [ "$LINES" -gt 350 ]; then
    WARNINGS="$WARNINGS\n  ⚠️  $(basename $FILE) is $LINES lines — approaching 400 line limit."
fi

# Check for float usage in Python financial files
if echo "$FILE" | grep -q '\.py$'; then
    FLOAT_COUNT=$(grep -cE 'float\(|: float' "$FILE" 2>/dev/null || echo 0)
    if [ "$FLOAT_COUNT" -gt 0 ]; then
        # Check if it's in a financial context
        if grep -qiE 'price|nav|amount|value|balance|portfolio|fund|money|decimal|rupee|inr' "$FILE" 2>/dev/null; then
            WARNINGS="$WARNINGS\n  🚫 FLOAT IN FINANCIAL CODE: $(basename $FILE) has $FLOAT_COUNT float references. Use Decimal."
        fi
    fi

    # Check for missing type hints on functions
    FUNC_COUNT=$(grep -cE '^\s*def ' "$FILE" 2>/dev/null || echo 0)
    TYPED_COUNT=$(grep -cE '^\s*def .*->|^\s*def .*:.*:' "$FILE" 2>/dev/null || echo 0)
    if [ "$FUNC_COUNT" -gt 0 ] && [ "$TYPED_COUNT" -lt "$FUNC_COUNT" ]; then
        MISSING=$((FUNC_COUNT - TYPED_COUNT))
        [ "$MISSING" -gt 2 ] && WARNINGS="$WARNINGS\n  ⚠️  $MISSING functions in $(basename $FILE) missing type hints."
    fi
fi

# Check for TypeScript 'any'
if echo "$FILE" | grep -qE '\.(ts|tsx)$'; then
    ANY_COUNT=$(grep -cE ': any\b|as any\b|<any>' "$FILE" 2>/dev/null || echo 0)
    if [ "$ANY_COUNT" -gt 0 ]; then
        WARNINGS="$WARNINGS\n  🚫 TYPESCRIPT 'any': $(basename $FILE) has $ANY_COUNT 'any' usages. Type everything."
    fi
fi

# Check for hardcoded secrets patterns
if grep -qiE '(api_key|apikey|secret|password|token)\s*=\s*["\x27][A-Za-z0-9+/=_-]{20,}' "$FILE" 2>/dev/null; then
    WARNINGS="$WARNINGS\n  🚫 POSSIBLE HARDCODED SECRET in $(basename $FILE). Use env vars."
fi

# Check for TODO comments
TODO_COUNT=$(grep -ciE '(TODO|FIXME|HACK|XXX):' "$FILE" 2>/dev/null || echo 0)
if [ "$TODO_COUNT" -gt 0 ]; then
    WARNINGS="$WARNINGS\n  ⚠️  $TODO_COUNT TODO/FIXME comments in $(basename $FILE). Resolve or track as issues."
fi

if [ -n "$WARNINGS" ]; then
    echo ""
    echo "═══ CODE QUALITY CHECK: $(basename $FILE) ═══"
    echo -e "$WARNINGS"
    echo ""
fi

exit 0
