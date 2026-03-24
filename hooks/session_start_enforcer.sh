#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SESSION START ENFORCER — Loads context and reminds about protocols
# SessionStart hook — fires when Claude session begins
# ═══════════════════════════════════════════════════════════════

PROJECT=$(basename "$(pwd)" 2>/dev/null)
MEMORY="$HOME/.claude/memory/SESSIONS.md"
CORPUS="$HOME/.claude/learning/BUG_CORPUS.md"
DECISIONS="$HOME/.claude/memory/DECISIONS.md"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  JIP ENGINEERING OS — Session Starting                      ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Project: $PROJECT"
echo "║  Time: $(date '+%Y-%m-%d %H:%M')"
echo "╠══════════════════════════════════════════════════════════════╣"

# Show last session state
LAST_SESSION=$(grep -A5 "Project:.*$PROJECT" "$MEMORY" 2>/dev/null | tail -6)
if [ -n "$LAST_SESSION" ]; then
    echo "║  Last session:"
    echo "$LAST_SESSION" | head -3 | sed 's/^/║    /'
fi

echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  MANDATORY PROTOCOLS (enforced by hooks):                   ║"
echo "║  1. TDD: Write tests FIRST — commit blocked without tests  ║"
echo "║  2. BUG_CORPUS: Check before coding (auto-reminded)        ║"
echo "║  3. Context7: Use before any library integration            ║"
echo "║  4. Session memory: Write summary BEFORE ending session     ║"
echo "║  5. Pytest loop: Fix until green, never hand back broken    ║"
echo "╠══════════════════════════════════════════════════════════════╣"

# Auto-deploy qa_config.yaml if this is a git repo without one
if [ -d ".git" ] && [ ! -f "qa_config.yaml" ]; then
    cp "$HOME/.claude/qa_agent/qa_config.yaml" ./qa_config.yaml 2>/dev/null
    echo "║  📋 Auto-deployed qa_config.yaml (QA now active)            ║"
fi

# Auto-create project dir for memory keeper
if [ -d ".git" ] && [ ! -d "project" ]; then
    mkdir -p project 2>/dev/null
fi

# Check for open QA issues
if [ -f "QA_REPORT.md" ]; then
    CRITICAL=$(grep -c "CRITICAL" QA_REPORT.md 2>/dev/null || echo 0)
    MAJOR=$(grep -c "MAJOR" QA_REPORT.md 2>/dev/null || echo 0)
    if [ "$CRITICAL" -gt 0 ] || [ "$MAJOR" -gt 0 ]; then
        echo "║  🚨 QA_REPORT.md: $CRITICAL CRITICAL, $MAJOR MAJOR — FIX FIRST ║"
    else
        echo "║  ✅ QA: No critical/major issues                           ║"
    fi
else
    echo "║  ⚠️  No QA_REPORT.md found                                  ║"
fi

echo "╚══════════════════════════════════════════════════════════════╝"
exit 0
