#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# BUG CAPTURE — Auto-captures error→fix patterns for learning
# PostToolUse hook for Bash — detects test failures and errors
# ═══════════════════════════════════════════════════════════════

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
STDOUT=$(echo "$INPUT" | jq -r '.stdout // empty' 2>/dev/null)
STDERR=$(echo "$INPUT" | jq -r '.stderr // empty' 2>/dev/null)
EXIT_CODE=$(echo "$INPUT" | jq -r '.exit_code // .exitCode // "0"' 2>/dev/null)

STATE_DIR="/tmp/claude_bug_tracking"
mkdir -p "$STATE_DIR"
PENDING="/tmp/claude_pending_capture.tmp"
PROJECT=$(basename "$(pwd)" 2>/dev/null)

# Track test failures
if echo "$CMD" | grep -qE '(pytest|npm test|npx jest|yarn test|cargo test)'; then
    if [ "$EXIT_CODE" != "0" ]; then
        # Save the failure state
        {
            echo "FAIL_TIME=$(date '+%Y-%m-%d %H:%M')"
            echo "FAIL_PROJECT=$PROJECT"
            echo "FAIL_CMD=$CMD"
            echo "FAIL_OUTPUT=$(echo "$STDOUT $STDERR" | tail -20)"
        } > "$STATE_DIR/last_failure"
        echo ""
        echo "🔴 Test failure recorded. Fix will be auto-captured for BUG_CORPUS."
    elif [ -f "$STATE_DIR/last_failure" ]; then
        # Tests now pass after a failure — capture the bug fix!
        source "$STATE_DIR/last_failure"
        DIFF=$(git diff HEAD~1 2>/dev/null | head -80)
        {
            echo "=== BUG FIX DETECTED ==="
            echo "Time: $(date '+%Y-%m-%d %H:%M')"
            echo "Project: $FAIL_PROJECT"
            echo "Failed cmd: $FAIL_CMD"
            echo "Was: $FAIL_OUTPUT"
            echo "Now: PASSING"
            echo "Diff:"
            echo "$DIFF"
        } > "$PENDING"
        rm -f "$STATE_DIR/last_failure"
        echo ""
        echo "📚 Bug fix captured → /tmp/claude_pending_capture.tmp"
        echo "   Will be written to BUG_CORPUS.md at session end."
    fi
fi

# Track general command failures for patterns
if [ "$EXIT_CODE" != "0" ] && echo "$CMD" | grep -qvE '(grep|test -|curl.*--max-time|which )'; then
    ERROR_HASH=$(echo "$CMD" | md5sum | cut -c1-8)
    TRACK_FILE="$STATE_DIR/error_${ERROR_HASH}"

    if [ -f "$TRACK_FILE" ]; then
        COUNT=$(cat "$TRACK_FILE")
        COUNT=$((COUNT + 1))
        echo "$COUNT" > "$TRACK_FILE"
        if [ "$COUNT" -ge 3 ]; then
            echo ""
            echo "⚠️  Same command failed $COUNT times: $CMD"
            echo "   STOP. Diagnose root cause before retrying."
        fi
    else
        echo "1" > "$TRACK_FILE"
    fi
fi

exit 0
