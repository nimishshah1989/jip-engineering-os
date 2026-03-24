#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# JIP Engineering OS — One-Command Installer
#
# Usage:
#   git clone https://github.com/YOUR_USER/jip-engineering-os.git
#   cd jip-engineering-os
#   bash install.sh
#
# What it does:
#   1. Backs up existing ~/.claude/ config
#   2. Installs 17 enforcement hooks
#   3. Installs 16 expert agents
#   4. Installs coding rules
#   5. Installs QA agent (autonomous testing)
#   6. Sets up memory/learning directories
#   7. Merges into existing settings.json (doesn't overwrite)
#   8. Installs QA agent Python dependencies
# ═══════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
BACKUP_DIR="$CLAUDE_DIR/backups/pre-jip-$(date +%Y%m%d-%H%M%S)"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  JIP Engineering OS — Installer                             ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  This will install:                                         ║"
echo "║  • 17 enforcement hooks (TDD, QA, security, memory, etc.)  ║"
echo "║  • 16 expert agents (architect, backend, frontend, CTO...)  ║"
echo "║  • 9 coding rules (style, security, testing, git, etc.)    ║"
echo "║  • Autonomous QA agent with 5 testing sub-agents           ║"
echo "║  • Bug learning corpus + session memory system              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── Pre-flight checks ───
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required. Install: brew install node"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "❌ jq required. Install: brew install jq"; exit 1; }

# ─── Backup ───
echo "📦 Backing up existing config to $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
[ -f "$CLAUDE_DIR/settings.json" ] && cp "$CLAUDE_DIR/settings.json" "$BACKUP_DIR/"
[ -d "$CLAUDE_DIR/hooks" ] && cp -r "$CLAUDE_DIR/hooks" "$BACKUP_DIR/"
[ -d "$CLAUDE_DIR/agents" ] && cp -r "$CLAUDE_DIR/agents" "$BACKUP_DIR/"
echo "  ✅ Backup complete"

# ─── Create directories ───
mkdir -p "$CLAUDE_DIR"/{hooks,agents,rules,learning,memory}

# ─── Install hooks ───
echo ""
echo "🔧 Installing hooks..."
cp "$SCRIPT_DIR/hooks/"* "$CLAUDE_DIR/hooks/"
chmod +x "$CLAUDE_DIR/hooks/"*.sh "$CLAUDE_DIR/hooks/"*.js 2>/dev/null
echo "  ✅ $(ls "$SCRIPT_DIR/hooks/" | wc -l | tr -d ' ') hooks installed"

# ─── Install agents ───
echo "🤖 Installing agents..."
cp "$SCRIPT_DIR/agents/"* "$CLAUDE_DIR/agents/"
echo "  ✅ $(ls "$SCRIPT_DIR/agents/" | wc -l | tr -d ' ') agents installed"

# ─── Install rules ───
echo "📏 Installing rules..."
cp "$SCRIPT_DIR/rules/"* "$CLAUDE_DIR/rules/"
echo "  ✅ $(ls "$SCRIPT_DIR/rules/" | wc -l | tr -d ' ') rules installed"

# ─── Install QA agent ───
echo "🔍 Installing QA agent..."
mkdir -p "$CLAUDE_DIR/qa_agent"/{agents,analysis,report,dashboard}
cp -r "$SCRIPT_DIR/qa_agent/"* "$CLAUDE_DIR/qa_agent/"
echo "  ✅ QA agent installed"

# ─── Install QA dependencies ───
echo "📦 Installing QA Python dependencies..."
pip3 install -q playwright pyyaml anthropic 2>/dev/null && echo "  ✅ Python deps installed" || echo "  ⚠️  pip install failed — run manually: pip3 install playwright pyyaml anthropic"
python3 -m playwright install chromium 2>/dev/null && echo "  ✅ Playwright chromium installed" || echo "  ⚠️  Playwright install failed — run: python3 -m playwright install chromium"

# ─── Set up memory/learning ───
echo "🧠 Setting up memory system..."
[ -f "$CLAUDE_DIR/memory/SESSIONS.md" ] || echo "# Session History" > "$CLAUDE_DIR/memory/SESSIONS.md"
[ -f "$CLAUDE_DIR/memory/DECISIONS.md" ] || echo "# Permanent Architectural Decisions" > "$CLAUDE_DIR/memory/DECISIONS.md"
[ -f "$CLAUDE_DIR/memory/PATTERNS.md" ] || echo "# Proven Code Patterns" > "$CLAUDE_DIR/memory/PATTERNS.md"
[ -f "$CLAUDE_DIR/learning/BUG_CORPUS.md" ] || cp "$SCRIPT_DIR/learning/BUG_CORPUS_TEMPLATE.md" "$CLAUDE_DIR/learning/BUG_CORPUS.md"
echo "  ✅ Memory system ready"

# ─── Merge settings.json ───
echo "⚙️  Configuring settings.json..."
SETTINGS="$CLAUDE_DIR/settings.json"

if [ ! -f "$SETTINGS" ]; then
    # Fresh install — write full settings
    cat > "$SETTINGS" << 'SETTINGS_EOF'
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/security_guardian.sh"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/commit_gate.sh"}]}
    ],
    "PostToolUse": [
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/post_write_validator.sh"}]},
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/test_reminder.sh"}]},
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/code_quality_gate.sh"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/bug_capture.sh"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/qa_auto_trigger.sh"}]},
      {"matcher": "Bash|Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": "node CLAUDE_HOOKS/memory_enforcer.js", "timeout": 5}]},
      {"matcher": "Bash|Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "node CLAUDE_HOOKS/qa_checkpoint.js", "timeout": 5}]},
      {"matcher": "Bash|Edit|Write|MultiEdit|Agent", "hooks": [{"type": "command", "command": "node CLAUDE_HOOKS/build_cycle_enforcer.js", "timeout": 5}]},
      {"matcher": "Bash|Edit|Write|MultiEdit|Agent|Task", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/memory_checkpoint.sh"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "CLAUDE_HOOKS/session_finalizer.sh"}]}
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "CLAUDE_HOOKS/session_start_enforcer.sh"}]}
    ]
  }
}
SETTINGS_EOF
    # Replace placeholder paths
    sed -i.bak "s|CLAUDE_HOOKS|$CLAUDE_DIR/hooks|g" "$SETTINGS" && rm -f "$SETTINGS.bak"
    echo "  ✅ Fresh settings.json created"
else
    echo "  ⚠️  Existing settings.json found — not overwriting."
    echo "     Your hooks from the backup are preserved."
    echo "     To get the full hook config, run: bash install.sh --force-settings"

    if [ "$1" = "--force-settings" ]; then
        cp "$BACKUP_DIR/settings.json" "$SETTINGS.user-backup"
        # Regenerate
        cat > "$SETTINGS" << 'SETTINGS_EOF'
{
  "permissions": {
    "allow": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)"]
  },
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/security_guardian.sh"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/commit_gate.sh"}]}
    ],
    "PostToolUse": [
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/post_write_validator.sh"}]},
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/test_reminder.sh"}]},
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/code_quality_gate.sh"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/bug_capture.sh"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/qa_auto_trigger.sh"}]},
      {"matcher": "Bash|Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": "node CLAUDE_HOOKS/memory_enforcer.js", "timeout": 5}]},
      {"matcher": "Bash|Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "node CLAUDE_HOOKS/qa_checkpoint.js", "timeout": 5}]},
      {"matcher": "Bash|Edit|Write|MultiEdit|Agent", "hooks": [{"type": "command", "command": "node CLAUDE_HOOKS/build_cycle_enforcer.js", "timeout": 5}]},
      {"matcher": "Bash|Edit|Write|MultiEdit|Agent|Task", "hooks": [{"type": "command", "command": "CLAUDE_HOOKS/memory_checkpoint.sh"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "CLAUDE_HOOKS/session_finalizer.sh"}]}
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "CLAUDE_HOOKS/session_start_enforcer.sh"}]}
    ]
  }
}
SETTINGS_EOF
        sed -i.bak "s|CLAUDE_HOOKS|$CLAUDE_DIR/hooks|g" "$SETTINGS" && rm -f "$SETTINGS.bak"
        echo "  ✅ Settings.json replaced (backup at $SETTINGS.user-backup)"
    fi
fi

# ─── Install CLAUDE.md template ───
if [ ! -f "$CLAUDE_DIR/CLAUDE.md" ]; then
    cp "$SCRIPT_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
    echo "  ✅ CLAUDE.md installed"
else
    echo "  ⚠️  Existing CLAUDE.md preserved (template at $SCRIPT_DIR/CLAUDE.md)"
fi

# ─── Done ───
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ JIP Engineering OS installed!                           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                             ║"
echo "║  What's active now:                                         ║"
echo "║  • git commit BLOCKED without tests                        ║"
echo "║  • Code quality checks on every file write                 ║"
echo "║  • Bug learning auto-capture                               ║"
echo "║  • Session memory enforcement                              ║"
echo "║  • QA auto-trigger after commits                           ║"
echo "║  • Build cycle tracking (plan→build→review→deploy)         ║"
echo "║  • Security guardian (blocks destructive commands)          ║"
echo "║                                                             ║"
echo "║  Start Claude Code in any project. Everything is automatic. ║"
echo "║                                                             ║"
echo "║  Optional: Install RTK for token savings:                   ║"
echo "║    brew install reachingforthejack/tap/rtk                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
