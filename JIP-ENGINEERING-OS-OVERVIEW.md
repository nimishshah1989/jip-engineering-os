# JIP Engineering OS — Complete Capability Overview

## What Is This?

A complete enforcement system that turns Claude Code from a smart but unreliable intern into a disciplined engineering team. It enforces testing, code quality, code review, QA, session memory, and bug learning — automatically, through hooks that Claude cannot bypass.

**Works on:** Claude Code CLI, Claude Code in VS Code, Claude Code in JetBrains
**Does NOT work on:** claude.ai, Claude Desktop app, Claude mobile app

**Install:**
```bash
git clone https://github.com/nimishshah1989/jip-engineering-os.git
cd jip-engineering-os
bash install.sh
```

---

## Without the System vs. With the System

| What Happens | Without JIP Engineering OS | With JIP Engineering OS |
|---|---|---|
| **You ask Claude to build a feature** | Claude jumps straight into coding. No plan, no structure. Writes whatever comes to mind first. | Claude first creates an architecture plan, then builds backend + frontend in parallel, then gets a fresh-eyes code review, then runs QA, then gets CTO sign-off — only THEN deploys. |
| **Tests** | Zero. Claude writes code and commits it without a single test. You discover bugs in production. | Claude is **physically blocked** from committing code without test files. The hook exits with an error. Tests are written first, every time. |
| **Code quality** | Files grow to 800-1000 lines. `any` everywhere in TypeScript. `float` used for money calculations (causes rounding errors). Secrets hardcoded in code. | Every file write is checked in real-time: file >400 lines? Flagged. `float` in financial code? Flagged. TypeScript `any`? Flagged. Hardcoded secret? Flagged. |
| **Bugs repeat** | Claude fixes a bug today. Next week, same bug in a different file. No memory of what went wrong. | Every bug fix is auto-captured into a learning corpus. Next session, Claude reads the corpus BEFORE writing code and applies the fix pre-emptively. |
| **Session memory** | You close the terminal. Everything Claude knew about your project is gone. Next session starts from zero — you re-explain everything. | Session state is saved to persistent files. Next session auto-loads: what was built, what decisions were made, what's next, what QA issues are open. |
| **Code review** | Claude reviews its own code. Finds nothing wrong (obviously — it just wrote it). | A **separate agent** reviews the code with fresh eyes. It doesn't know why decisions were made — it only sees what's actually there. Catches real bugs. |
| **QA / Testing the actual app** | Never happens. You manually click around and find broken buttons. | An autonomous QA agent launches a browser, clicks every button, fuzzes every form, tests every user flow, takes screenshots at 3 screen sizes, and writes a detailed report with reproduction steps. |
| **Dangerous commands** | Claude might run `rm -rf`, `DROP TABLE`, or expose your API keys. | Security hook blocks destructive SQL, dangerous file operations, and infrastructure destruction before they execute. |
| **Deploying** | Claude deploys whenever you say "deploy". No checks. | Deploy is blocked unless: tests pass, code review passed, CTO agent approved. No shortcuts. |
| **Context runs out mid-session** | Claude's memory fills up. Everything it was working on is lost. You start over. | At 50% context, Claude is reminded to save. At 65%, it's nagged every 3 tool calls. At 75%, it's told on EVERY action. Session state is preserved regardless. |
| **Starting a new project** | Empty slate. No standards. Quality depends on luck. | QA config auto-deploys, all hooks activate immediately, session enforcer shows the protocols. Same quality bar from day one. |
| **Multiple files need building** | Claude builds one file at a time, sequentially. Slow. | Backend and frontend agents launch in **parallel**. Independent work happens simultaneously. |
| **You come back after a week** | "I don't know what this project is." Claude has to re-read everything. Makes contradictory decisions. | Reads project summary + session history + decisions log. Picks up exactly where you left off. Respects past architectural decisions. |

---

## The 17 Enforcement Hooks

These run automatically. You don't invoke them. They fire on every tool call Claude makes.

| # | Hook | What It Does | How It's Enforced |
|---|------|-------------|-------------------|
| 1 | **Commit Gate** | Blocks git commits if changed code files have no corresponding test files | Hook exits with error — commit physically cannot happen |
| 2 | **Test Reminder** | Warns every time a code file is written without a test file | Message appears after every file write |
| 3 | **Code Quality Gate** | Checks every file for: >400 lines, float in money code, TypeScript `any`, hardcoded secrets, TODO comments | Runs on every file write, shows warnings |
| 4 | **Bug Auto-Capture** | Detects when tests go from failing to passing and records the bug + fix | Automatic — no action needed |
| 5 | **Bug Learning Corpus** | Library of past bugs that Claude reads before writing new code | Checked at session start, grows over time |
| 6 | **QA Auto-Trigger** | Runs autonomous browser-based QA testing after commits with 3+ changed files | Automatic after git commit |
| 7 | **QA Agent** | 5 sub-agents: page discovery, button/link testing, form fuzzing, user flow walking, visual inspection | Writes a QA report with severity ratings and fix suggestions |
| 8 | **Security Guardian** | Blocks: `rm -rf /`, `DROP TABLE`, `DELETE FROM ... WHERE 1=1`, AWS infrastructure destruction | Hook blocks the command before it runs |
| 9 | **Memory Enforcer** | Forces Claude to save session summary before context fills up (nags at 50%, 65%, 75%) | Injects warnings into conversation that Claude must act on |
| 10 | **Session Start Enforcer** | Loads last session context, shows QA status, auto-deploys QA config to new projects | Runs automatically when you start Claude Code |
| 11 | **Session Finalizer** | Flushes bug captures to learning corpus, auto-generates project summary, runs QA if server available | Runs automatically when session ends |
| 12 | **Build Cycle Enforcer** | Tracks whether Claude followed the plan→build→review→QA→deploy pipeline. Warns on violations. | Monitors all tool calls, injects warnings |
| 13 | **Memory Checkpoint** | Periodic reminder every 50 tool calls to save session state | Counts tool calls, reminds when due |
| 14 | **Post-Write Validator** | Runs TypeScript type-checking after every file write | Automatic after every code change |
| 15 | **QA Checkpoint** | Reminds about QA after 5+ files changed or 20+ edits without running tests | Tracks changes, reminds at milestones |
| 16 | **Master Orchestrator Agent** | Dispatches expert agents in order: architect → backend + frontend → code review → QA → CTO → deploy | Say "build [feature]" and it runs the full pipeline |
| 17 | **Retrofit Auditor Agent** | Scans existing projects for quality issues, produces scored report with prioritised fix plan | Say "retrofit this project" in any codebase |

---

## The 16 Expert Agents

Each agent is a specialist with deep domain knowledge. They are dispatched by the orchestrator or invoked individually.

| Agent | Expertise | When It's Used |
|-------|----------|---------------|
| **Orchestrator** | Pipeline coordination — dispatches all other agents in the correct order | Any non-trivial feature ("build X") |
| **Architect** | System design, API contracts, data models, file structure | Before any code is written |
| **Backend** | Python, FastAPI, databases, Decimal math, Pydantic models | Building server-side code |
| **Frontend** | Next.js, React, TypeScript, CSS, responsive design | Building user interfaces |
| **Code Reviewer** | Bug detection, security holes, correctness, edge cases | After code is written — uses fresh eyes (separate agent, not the one that wrote it) |
| **CTO** | Architecture integrity, long-term health, veto power | Before any deploy — can APPROVE or BLOCK |
| **DevOps** | Docker, Nginx, server deployment, CI/CD | Deploy step |
| **QA** | QA report interpretation, fix prioritisation | After autonomous QA runs |
| **Verifier** | Adversarial testing — wrong inputs, edge cases, auth bypass attempts | After code review passes |
| **Memory Keeper** | Session state, project summaries, decision logs | End of every session |
| **Retrofit Auditor** | Code quality audits, test gap analysis, remediation plans | Auditing existing projects |
| **Project Init** | New project scaffolding, config, directory structure | First session of any new project |
| **Planner** | Implementation planning for complex multi-step features | Before multi-step work |
| **TDD Guide** | Test-driven development methodology and enforcement | During all coding |
| **General Code Reviewer** | General-purpose code review for any language | After any code changes |
| **Security Reviewer** | Vulnerability detection, OWASP top 10, secret scanning | Before commits touching auth, user input, or APIs |

---

## The Build Pipeline (How Features Get Built)

```
You say: "Build [feature]"
         │
         ▼
┌─────────────────┐
│  1. ARCHITECT    │  Creates a plan — API design, data models, file structure
│     (plan only)  │  No code is written yet
└────────┬────────┘
         │ Plan approved
         ▼
┌─────────────────┐  ┌─────────────────┐
│  2a. BACKEND    │  │  2b. FRONTEND   │  Build in PARALLEL
│  Python/FastAPI │  │  Next.js/React  │  Tests written FIRST (TDD)
│  Tests first    │  │  Tests first    │  commit_gate enforces this
└────────┬────────┘  └────────┬────────┘
         │                    │
         ▼                    ▼
┌──────────────────────────────┐
│  3. CODE REVIEW              │  SEPARATE agent with fresh eyes
│  Checks: bugs, security,    │  Did not write the code
│  edge cases, patterns        │  Verdict: PASS or NEEDS CHANGES
└────────┬─────────────────────┘
         │ PASS
         ▼
┌──────────────────────────────┐
│  4. QA LOOP                  │  Autonomous browser testing
│  Clicks every button         │  Fuzzes every form
│  Tests every user flow       │  Screenshots at 3 viewports
│  Report: CRITICAL/MAJOR/     │  Loops until clean
│          MINOR issues        │
└────────┬─────────────────────┘
         │ Clean
         ▼
┌──────────────────────────────┐
│  5. CTO SIGN-OFF             │  Architecture review
│  Verdict: APPROVE / BLOCK    │  BLOCK = nothing ships
└────────┬─────────────────────┘
         │ APPROVE
         ▼
┌──────────────────────────────┐
│  6. DEPLOY                   │  Docker build, server push
│  Nginx config, health check  │  Only after all gates pass
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  7. SAVE STATE               │  Session summary written
│  Project state persisted     │  Bug captures flushed
│  Ready for next session      │  Decision log updated
└──────────────────────────────┘
```

---

## The Learning Loop (How Claude Gets Smarter Over Time)

```
Session 1: Claude writes code → test fails → Claude fixes it → test passes
                                                    │
                                            bug_capture.sh detects
                                            the fail→pass transition
                                                    │
                                                    ▼
                                         Bug + fix saved to
                                         BUG_CORPUS.md
                                                    │
Session 2: Claude starts coding ◄───────────────────┘
           Reads BUG_CORPUS first
           Applies the fix PRE-EMPTIVELY
           Bug never happens again
```

---

## One-Line Summary

**Without the system:** Claude is a smart intern with no rules — fast but unreliable, forgets everything, ships untested code, repeats mistakes.

**With the system:** Claude is a senior engineering team with enforced standards — plans before coding, writes tests first, gets code reviewed by a separate agent, runs QA automatically, remembers everything across sessions, learns from every bug, and cannot ship without approval.

---

## GitHub Repository

**https://github.com/nimishshah1989/jip-engineering-os**

Install: `git clone` → `bash install.sh` → done.
