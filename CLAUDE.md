# CLAUDE.md — JIP Engineering OS
**Read this first. Every session. No exceptions.**

---

## Session Start (enforced by session_start_enforcer.sh hook)

The hook auto-loads your last session state. You must:
1. Read ./project/summary.md (where last session left off)
2. Check ./QA_REPORT.md — CRITICAL or MAJOR issues = fix FIRST
3. Confirm: "Ready. [Project]. Last state: [summary]. QA: [status]."

---

## TDD — Enforced by commit_gate.sh (BLOCKS commits without tests)

1. Write test file FIRST (test_*.py or *.test.ts)
2. Run test — it MUST fail (RED)
3. Write implementation (GREEN)
4. Run: `pytest tests/ -x -q` or `npm test`
5. Fix until green. NEVER stop on a failing test.
6. NOW you can commit.

---

## Hooks That Enforce This (17 active in settings.json)

| Hook | Type | Action |
|------|------|--------|
| commit_gate.sh | PreToolUse | BLOCKS git commit without test files |
| test_reminder.sh | PostToolUse | WARNS when writing code without tests |
| code_quality_gate.sh | PostToolUse | Checks file size (400 max), float, TS any, secrets, TODOs |
| bug_capture.sh | PostToolUse | Auto-captures test fail→pass patterns for learning |
| qa_auto_trigger.sh | PostToolUse | Runs QA after git commit with 3+ files |
| memory_enforcer.js | PostToolUse | Nags at 50/65/75% context to save session summary |
| qa_checkpoint.js | PostToolUse | QA reminders after significant changes |
| build_cycle_enforcer.js | PostToolUse | Warns on code-without-plan, deploy-without-review |
| memory_checkpoint.sh | PostToolUse | Periodic session save reminders |
| security_guardian.sh | PreToolUse | Blocks destructive SQL/rm -rf/AWS destroy |
| session_start_enforcer.sh | SessionStart | Loads context, auto-deploys qa_config.yaml |
| session_finalizer.sh | Stop | Flushes bug captures, generates project/summary.md |

---

## Agent Pipeline (orchestrated by jip-orchestrator)

For any non-trivial feature, the orchestrator runs:
```
jip-architect (plan) → jip-backend + jip-frontend (parallel build) →
jip-code-review (fresh eyes) → QA loop → jip-cto (sign-off) → jip-devops (deploy)
```

---

## Session End — BEFORE stopping

1. Write to ~/.claude/memory/SESSIONS.md:
   [DATE] [PROJECT] — [done] | Decisions: [any] | Bugs: [any] | Next: [step]
2. The session_finalizer hook flushes bug captures and generates project/summary.md

---

## Absolute Rules

- **Decimal** always for financial values, never float
- **No file over 400 lines** — split before the limit
- **No `any` in TypeScript** — type everything
- **No hardcoded secrets** — env vars only
- **No TODO comments** in committed code
- **Tests before commits** — enforced by hook
