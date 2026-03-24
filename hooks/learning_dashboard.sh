#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# LEARNING DASHBOARD — Shows bug corpus health and learning stats
# Run manually: ~/.claude/hooks/learning_dashboard.sh
# ═══════════════════════════════════════════════════════════════

CORPUS="$HOME/.claude/learning/BUG_CORPUS.md"
PENDING="/tmp/claude_pending_capture.tmp"
TRACKER="/tmp/claude_bug_tracking"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  LEARNING DASHBOARD — Bug Corpus Health                     ║"
echo "╠══════════════════════════════════════════════════════════════╣"

# Corpus stats
if [ -f "$CORPUS" ]; then
    TOTAL=$(grep -c '^\-\-\-$' "$CORPUS" 2>/dev/null || echo 0)
    CATEGORIES=$(grep -oE 'Category: [a-z-]+' "$CORPUS" 2>/dev/null | sort | uniq -c | sort -rn)
    LATEST=$(grep -oE '\[202[0-9]-Q[1-4]\]' "$CORPUS" 2>/dev/null | tail -1)
    echo "║  Total entries    : $TOTAL"
    echo "║  Latest entry     : $LATEST"
    echo "║  By category:"
    echo "$CATEGORIES" | while read COUNT CAT; do
        printf "║    %-20s %s\n" "$CAT" "$COUNT"
    done
else
    echo "║  ❌ BUG_CORPUS.md not found!"
fi

echo "╠══════════════════════════════════════════════════════════════╣"

# Pending captures
if [ -f "$PENDING" ] && [ -s "$PENDING" ]; then
    echo "║  📦 PENDING CAPTURE (not yet flushed):"
    head -5 "$PENDING" | sed 's/^/║    /'
else
    echo "║  No pending captures"
fi

echo "╠══════════════════════════════════════════════════════════════╣"

# Active failure tracking
if [ -d "$TRACKER" ] && [ -f "$TRACKER/last_failure" ]; then
    echo "║  🔴 ACTIVE FAILURE being tracked:"
    head -3 "$TRACKER/last_failure" | sed 's/^/║    /'
else
    echo "║  No active failure tracking"
fi

echo "╠══════════════════════════════════════════════════════════════╣"

# Repeated errors
if [ -d "$TRACKER" ]; then
    REPEATS=$(find "$TRACKER" -name "error_*" -exec cat {} \; 2>/dev/null | awk '$1 >= 3 {sum++} END {print sum+0}')
    echo "║  Repeated errors (3+ times): $REPEATS"
fi

echo "╚══════════════════════════════════════════════════════════════╝"
