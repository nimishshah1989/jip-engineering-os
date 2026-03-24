#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# QA AUTO-TRIGGER — Runs QA agent after significant commits
# PostToolUse hook for Bash — triggers after git commit
# ═══════════════════════════════════════════════════════════════

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
[ -z "$CMD" ] && CMD="$INPUT"

# Only trigger on git commit
echo "$CMD" | grep -qE '^\s*git\s+commit' || exit 0

# Only if qa_config.yaml exists in project
[ -f "qa_config.yaml" ] || exit 0

# Count files changed in this commit
FILES_CHANGED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | wc -l | tr -d ' ')
[ "$FILES_CHANGED" -lt 3 ] && exit 0

# Find a running server
TARGET=""
for PORT in 3000 3001 8000 8001 8002 8003 8004 8005 8006 8007 8008; do
    if curl -s --max-time 1 "http://localhost:$PORT" >/dev/null 2>&1; then
        TARGET="http://localhost:$PORT"
        break
    fi
done

# Try deployed URL from qa_config
if [ -z "$TARGET" ]; then
    TARGET=$(grep -oE 'deployed_url:\s*\S+' qa_config.yaml 2>/dev/null | awk '{print $2}' | tr -d '"')
    if [ -n "$TARGET" ]; then
        curl -s --max-time 2 "$TARGET" >/dev/null 2>&1 || TARGET=""
    fi
fi

if [ -n "$TARGET" ]; then
    echo ""
    echo "🔍 QA AUTO-TRIGGER: $FILES_CHANGED files changed. Running QA against $TARGET..."
    # Run in background so it doesn't block the session
    nohup python3 ~/.claude/qa_agent/run.py --target "$TARGET" --report QA_REPORT.md >/tmp/qa_last_run.log 2>&1 &
    echo "   QA running in background (PID $!). Results → QA_REPORT.md"
else
    echo ""
    echo "📋 QA REMINDER: $FILES_CHANGED files changed in commit."
    echo "   No server detected. Start server, then run:"
    echo "   python3 ~/.claude/qa_agent/run.py --target http://localhost:[PORT]"
fi

exit 0
