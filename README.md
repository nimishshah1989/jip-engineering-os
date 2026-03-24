# JIP Engineering OS

A complete enforcement system for Claude Code that ensures high-quality code through hooks, expert agents, and automated QA.

## What It Does

- **Blocks commits without tests** (TDD enforced, not suggested)
- **Auto-runs QA** after every significant commit
- **Checks code quality** in real-time (file size, type safety, secrets, complexity)
- **Captures bugs automatically** and builds a learning corpus
- **Saves session memory** so context survives across days/weeks
- **Orchestrates 16 expert agents** in the right order (plan → build → review → QA → deploy)
- **Guards against destructive commands** (rm -rf, DROP TABLE, etc.)

## Install

```bash
git clone https://github.com/YOUR_USER/jip-engineering-os.git
cd jip-engineering-os
bash install.sh
```

That's it. Start Claude Code in any project — everything is automatic.

## What Gets Installed

```
~/.claude/
├── hooks/              # 14 enforcement hooks (bash + node.js)
│   ├── commit_gate.sh          # Blocks commits without tests
│   ├── test_reminder.sh        # Warns on untested code writes
│   ├── code_quality_gate.sh    # File size, float, TS any, secrets
│   ├── bug_capture.sh          # Auto-captures error→fix patterns
│   ├── qa_auto_trigger.sh      # Runs QA after commits
│   ├── memory_enforcer.js      # Saves session state before context expires
│   ├── qa_checkpoint.js        # QA reminders at milestones
│   ├── build_cycle_enforcer.js # Tracks agent pipeline
│   ├── memory_checkpoint.sh    # Periodic memory reminders
│   ├── security_guardian.sh    # Blocks destructive commands
│   ├── post_write_validator.sh # TypeScript type checks
│   ├── session_start_enforcer.sh  # Loads context at session start
│   ├── session_finalizer.sh    # Saves state at session end
│   └── learning_dashboard.sh   # View bug corpus health
├── agents/             # 16 expert agent prompts
│   ├── jip-orchestrator.md     # Master pipeline orchestrator
│   ├── jip-architect.md        # System design (plan before code)
│   ├── jip-backend.md          # FastAPI/Python specialist
│   ├── jip-frontend.md         # Next.js/React specialist
│   ├── jip-code-review.md      # Fresh-eyes code review
│   ├── jip-cto.md              # Architecture sign-off (veto power)
│   ├── jip-devops.md           # Docker/Nginx/deploy
│   ├── jip-qa.md               # QA report reader + fix loop
│   ├── jip-verifier.md         # Adversarial testing
│   ├── jip-memory-keeper.md    # Session state persistence
│   ├── jip-retrofit.md         # Audit existing codebases
│   └── project-init.md         # New project setup
├── rules/              # 9 coding standard files
├── qa_agent/           # Autonomous QA testing system
│   ├── run.py                  # Main entry point
│   ├── agents/                 # 5 testing sub-agents
│   ├── analysis/               # Claude-powered issue classifier
│   ├── report/                 # QA_REPORT.md generator
│   └── dashboard/              # Live QA dashboard (localhost:8765)
├── learning/           # Bug corpus (grows over time)
├── memory/             # Session history + decisions + patterns
├── settings.json       # Hook registration (auto-configured)
└── CLAUDE.md           # Master instructions
```

## How It Works

### Every Session
1. **SessionStart hook** loads your last context, shows QA status, auto-deploys qa_config.yaml
2. **During coding**: hooks check every file write for quality issues, remind about tests
3. **On commit**: commit_gate BLOCKS if test files are missing
4. **After commit**: QA agent auto-runs if 3+ files changed
5. **At 50% context**: memory_enforcer reminds to save session summary
6. **Session end**: finalizer flushes bug captures, generates project summary

### Build Cycle (for features)
Say "build [feature]" → jip-orchestrator dispatches:
1. **jip-architect** → produces plan (no code yet)
2. **jip-backend + jip-frontend** → parallel implementation with TDD
3. **jip-code-review** → separate agent, fresh eyes
4. **QA loop** → autonomous testing
5. **jip-cto** → architecture sign-off (can BLOCK)
6. **jip-devops** → deploy

### Bug Learning
- Test fails → bug_capture.sh records the failure
- You fix it → tests pass → capture auto-written to BUG_CORPUS.md
- Next session → Claude reads corpus, applies fixes pre-emptively

## Works On

- **Claude Code CLI** ✅
- **Claude Code in VS Code** ✅
- **Claude Code in JetBrains** ✅

All use the same `~/.claude/` directory.

## Customisation

- Edit `~/.claude/CLAUDE.md` to add project-specific rules
- Edit `~/.claude/agents/*.md` to customise agent behaviour
- Edit `qa_config.yaml` in each project root for QA settings
- Add entries to `~/.claude/memory/DECISIONS.md` for permanent rules
- Add entries to `~/.claude/learning/BUG_CORPUS.md` for known bugs

## Uninstall

```bash
# Restore from backup
cp ~/.claude/backups/pre-jip-*/settings.json ~/.claude/settings.json
```

## License

MIT
