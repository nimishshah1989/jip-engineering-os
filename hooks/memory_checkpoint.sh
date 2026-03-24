#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# MEMORY CHECKPOINT — Reminds Claude to save session state
# PostToolUse hook for Agent — fires after subagent completes
# Also counts total tool calls and reminds at intervals
# ═══════════════════════════════════════════════════════════════

COUNTER_FILE="/tmp/claude_tool_counter"
MEMORY_FILE="$HOME/.claude/memory/SESSIONS.md"
PROJECT=$(basename "$(pwd)" 2>/dev/null)

# Increment counter
COUNT=0
[ -f "$COUNTER_FILE" ] && COUNT=$(cat "$COUNTER_FILE")
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Every 50 tool calls, remind about session memory
if [ $((COUNT % 50)) -eq 0 ]; then
    # Check if a real summary exists for this session
    TODAY=$(date '+%Y-%m-%d')
    HAS_SUMMARY=$(grep "$TODAY.*$PROJECT.*Decisions:" "$MEMORY_FILE" 2>/dev/null | wc -l)

    if [ "$HAS_SUMMARY" -eq 0 ]; then
        echo ""
        echo "═══════════════════════════════════════════"
        echo "💾 MEMORY CHECKPOINT ($COUNT tool calls)"
        echo "   No session summary written yet."
        echo "   Write to SESSIONS.md NOW before context fills up:"
        echo "   [DATE] [PROJECT] — [done] | Decisions: | Bugs: | Next:"
        echo "═══════════════════════════════════════════"
    fi
fi

exit 0
