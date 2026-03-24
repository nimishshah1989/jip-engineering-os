#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SESSION FINALIZER — Enforces memory persistence at session end
# Stop hook — fires when Claude session ends
# ═══════════════════════════════════════════════════════════════

MEMORY="$HOME/.claude/memory/SESSIONS.md"
PENDING="/tmp/claude_pending_capture.tmp"
CORPUS="$HOME/.claude/learning/BUG_CORPUS.md"
PROJECT=$(basename "$(pwd)" 2>/dev/null)
NOW=$(date '+%Y-%m-%d %H:%M')

# ─── Write session stub (Claude should have written the real entry already) ───
# Check if Claude already wrote a detailed entry in the last 5 minutes
RECENT_ENTRY=$(tail -20 "$MEMORY" 2>/dev/null | grep -c "Decisions:\|Next:\|Bugs fixed:")
if [ "$RECENT_ENTRY" -eq 0 ]; then
    # No detailed entry found — write stub AND loud warning
    { echo ""; echo "---"; echo "**Session ended:** $NOW | Project: $PROJECT";
      echo "⚠️ NO SUMMARY WRITTEN — Claude failed to run session-end protocol"; } >> "$MEMORY"
fi

# ─── Auto-generate project/summary.md if Claude didn't ───
if [ -d ".git" ] && [ ! -f "project/summary.md" ] || [ -f "project/summary.md" ]; then
    mkdir -p project 2>/dev/null
    LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "no commits")
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    FILES_MODIFIED=$(git diff --stat HEAD~3 2>/dev/null | tail -1 || echo "unknown")
    QA_STATUS="not run"
    [ -f "QA_REPORT.md" ] && QA_STATUS=$(grep -oE '(PASSED|CRITICAL|MAJOR)' QA_REPORT.md 2>/dev/null | head -1 || echo "exists")

    # Only write auto-summary if Claude didn't write one this session
    SUMMARY_AGE=$(( $(date +%s) - $(stat -f %m project/summary.md 2>/dev/null || echo 0) ))
    if [ "$SUMMARY_AGE" -gt 300 ] 2>/dev/null; then
        cat > /tmp/claude_auto_summary.md << EOSUMMARY
# $PROJECT — Auto-Generated Summary
_Last updated: $NOW (auto-generated — Claude did not write a proper summary)_

## Current state
Branch: $BRANCH | Last commit: $LAST_COMMIT
Recent changes: $FILES_MODIFIED
QA: $QA_STATUS

## Next session starts here
**First thing to do:** Check this auto-summary and write a proper project/summary.md
**QA status:** $QA_STATUS
EOSUMMARY
        # Only overwrite if existing summary is older than 1 hour
        if [ "$SUMMARY_AGE" -gt 3600 ] 2>/dev/null; then
            cp /tmp/claude_auto_summary.md project/summary.md 2>/dev/null
        fi
    fi
fi

# ─── Auto-flush pending bug captures to BUG_CORPUS ───
if [ -f "$PENDING" ] && [ -s "$PENDING" ]; then
    echo "" >> "$CORPUS"
    echo "---" >> "$CORPUS"
    cat "$PENDING" >> "$CORPUS"
    rm -f "$PENDING"
    echo "📚 Bug capture flushed to BUG_CORPUS.md"
fi

# ─── Clean up session temp files ───
rm -f /tmp/claude_test_reminded_* 2>/dev/null
rm -f /tmp/claude_bug_tracking/error_* 2>/dev/null

# ─── QA check (try deployed URL if localhost not available) ───
QA_RAN=false
if [ -f "qa_config.yaml" ]; then
    # Try localhost first
    for PORT in 3000 3001 8000 8001 8002 8003 8004 8005; do
        if curl -s --max-time 2 "http://localhost:$PORT" >/dev/null 2>&1; then
            python3 ~/.claude/qa_agent/run.py --target "http://localhost:$PORT" 2>/dev/null && QA_RAN=true
            break
        fi
    done

    # Try deployed URL from qa_config if localhost failed
    if [ "$QA_RAN" = false ]; then
        DEPLOYED_URL=$(grep -oP 'deployed_url:\s*\K.*' qa_config.yaml 2>/dev/null | tr -d ' "')
        if [ -n "$DEPLOYED_URL" ]; then
            curl -s --max-time 3 "$DEPLOYED_URL" >/dev/null 2>&1 && \
                python3 ~/.claude/qa_agent/run.py --target "$DEPLOYED_URL" 2>/dev/null && QA_RAN=true
        fi
    fi
fi

# ─── Final enforcement message ───
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  SESSION END CHECKLIST                                      ║"
echo "╠══════════════════════════════════════════════════════════════╣"

if [ "$RECENT_ENTRY" -gt 0 ]; then
    echo "║  ✅ Session summary written to SESSIONS.md                  ║"
else
    echo "║  ❌ SESSIONS.md — NO SUMMARY (Claude must write one!)       ║"
fi

if [ -f "$PENDING" ]; then
    echo "║  ❌ Pending bug capture NOT flushed                         ║"
else
    echo "║  ✅ Bug captures flushed                                    ║"
fi

if [ "$QA_RAN" = true ]; then
    echo "║  ✅ QA loop executed                                        ║"
else
    echo "║  ⚠️  QA skipped (no server found)                           ║"
fi

echo "╚══════════════════════════════════════════════════════════════╝"
exit 0
