# JIP Engineering OS — Complete Guide

## What Is This?

An enforcement system for Claude Code that makes AI-assisted coding reliable and high-quality. Instead of hoping Claude writes good code, this system **forces** it — through hooks that block bad commits, agents that review code with fresh eyes, and automated QA that tests your app in a real browser.

**One-command install:**
```bash
git clone https://github.com/nimishshah1989/jip-engineering-os.git
cd jip-engineering-os
bash install.sh
```

After install, open Claude Code in any project. Everything activates automatically.

---

## What You Need To Know: Automatic vs. Manual

### Things That Happen AUTOMATICALLY (you do nothing)

These fire on their own. You never call them. They just work.

| What | When It Fires | What It Does |
|------|--------------|-------------|
| **Session context loader** | Every time you start Claude Code | Shows your last session state, what project you were working on, what's next, whether there are open QA issues. Auto-creates QA config for new projects. |
| **Commit blocker** | Every time Claude tries `git commit` | Checks if every changed `.py` / `.ts` / `.tsx` file has a corresponding test file. If not, the commit is **blocked**. Claude must write tests first. Commits for `docs:` or `chore:` are allowed through. |
| **Test reminder** | Every time Claude writes or edits a code file | If the file has no test file (e.g. `app.py` exists but `test_app.py` doesn't), Claude sees a warning: "NO TESTS for app.py — write tests first." One reminder per file, not spammy. |
| **Code quality checker** | Every time Claude writes or edits a code file | Checks: Is the file over 400 lines? Is `float` used in financial calculations (should be `Decimal`)? Is TypeScript `any` used (should be typed)? Are there hardcoded API keys/secrets? Are there TODO comments? Shows warnings for each violation. |
| **Bug auto-capture** | Every time Claude runs tests | If tests fail and then pass after a fix, the bug + fix is automatically recorded. You build a "bug library" over time that Claude reads before writing new code — so the same bug never happens twice. |
| **QA auto-trigger** | After every `git commit` that changes 3+ files | If a web server is running (checks ports 3000-8008), launches the full QA agent: browser automation that clicks every button, tests every form, walks every user flow, takes screenshots, and writes a report. |
| **Security guardian** | Every time Claude runs a bash command | Blocks dangerous commands before they execute: `rm -rf /`, `DROP TABLE`, `DELETE FROM ... WHERE 1=1`, AWS `terminate-instance`, `chmod 777 /`. |
| **Memory enforcer** | Continuously during the session | At 50% context used: gentle reminder to save session state. At 65%: reminds every 3 actions. At 75%: reminds on every single action. Stops nagging once you've saved. |
| **Memory checkpoint** | Every 50 tool calls | Checks if a session summary has been written. If not, reminds Claude to save before context runs out. |
| **Build cycle tracker** | Continuously during the session | Tracks which expert agents have been used. Warns if: code is written without a plan (after 5+ files), deploy is attempted without code review, deploy is attempted without CTO sign-off. |
| **TypeScript type checker** | Every time Claude writes or edits a .ts/.tsx file | Runs `tsc --noEmit` to catch type errors immediately, not at build time. |
| **Session state saver** | When you end the session | Auto-flushes any captured bugs to the learning corpus. Auto-generates a project summary if Claude didn't write one. Checks if QA can run. Reports what was saved and what was missed. |
| **QA checkpoint reminder** | After significant work | After 5+ files changed since last reminder, or 20+ edits without running any tests, reminds Claude to run QA or tests. |

**Total: 14 things that happen automatically without you doing anything.**

---

### Things You Say To Trigger (simple phrases)

These require you to say something. But it's just a phrase — not a command to memorize.

| What You Say | What Happens |
|-------------|-------------|
| **"Build [feature description]"** | The master orchestrator launches. It runs the full pipeline: architect plans it → backend + frontend build in parallel → separate agent reviews the code → QA tests the app → CTO agent approves or blocks → deploy. You just describe what you want. |
| **"Retrofit this project"** | Runs a full audit of the current codebase. Checks: test coverage (which files have no tests), file sizes (which are too big), financial code using float instead of Decimal, TypeScript `any` usage, hardcoded secrets, dead code, TODO comments, dependency vulnerabilities. Produces a scored report with a prioritised fix list. |
| **"Fix the issues" / "Fix quality"** | After a retrofit report exists, Claude reads it and starts fixing — CRITICAL issues first, then MAJOR, then MINOR. Uses TDD (writes tests first for each fix). |

**That's it. Three phrases cover everything you'd actively trigger.**

---

### Things That Are Good To Know (but not required)

| What | How | When You'd Use It |
|------|-----|-------------------|
| **View bug learning health** | Run `~/.claude/hooks/learning_dashboard.sh` in terminal | To check if bugs are being captured and the corpus is growing |
| **Run QA manually** | `python3 ~/.claude/qa_agent/run.py --target http://localhost:3000` | If you want to run QA without committing, or against a specific URL |
| **View QA dashboard** | `python3 ~/.claude/qa_agent/dashboard/serve.py` → opens localhost:8765 | To see QA results in a visual dashboard |
| **Set deployed URL for QA** | Edit `qa_config.yaml` in project root, set `deployed_url: https://your-app.com` | So QA can test your deployed app when localhost isn't running |
| **Add a permanent decision** | Edit `~/.claude/memory/DECISIONS.md` | To record an architectural rule that should never be violated (e.g. "never use float for money") |
| **Add a known bug pattern** | Edit `~/.claude/learning/BUG_CORPUS.md` | To teach Claude about a bug you've seen so it never repeats it |

---

## The 16 Expert Agents

When the orchestrator runs (you said "build [feature]"), it dispatches these agents in order. You never invoke them individually — the orchestrator handles it.

| Agent | Role | What It's Expert At |
|-------|------|-------------------|
| **Orchestrator** | Dispatches all agents in the right order | Pipeline management — makes sure nothing is skipped |
| **Architect** | Plans before code is written | API design, data models, file structure, component hierarchy |
| **Backend** | Writes server-side code | Python, FastAPI, databases, financial math with Decimal, Pydantic validation |
| **Frontend** | Writes user-facing code | Next.js, React, TypeScript, CSS, responsive design, accessibility |
| **Code Reviewer** | Reviews code it did NOT write | Bugs, security holes, edge cases, missed error handling. Uses fresh eyes — separate agent from the one that wrote the code |
| **CTO** | Final authority before deploy | Architecture integrity, long-term maintainability. Can APPROVE or BLOCK. Block = nothing ships. |
| **DevOps** | Handles deployment | Docker, Nginx configuration, server setup, CI/CD pipelines |
| **QA** | Interprets QA reports | Reads the automated QA report, prioritises fixes, loops until clean |
| **Verifier** | Tries to break things | Sends wrong inputs, empty inputs, boundary values, auth bypass attempts. If it breaks, it fails the build. |
| **Memory Keeper** | Saves session state | Writes project summary so the next session picks up exactly where you left off |
| **Retrofit Auditor** | Audits existing code | Test gaps, oversized files, type safety, security, dependency health |
| **Project Init** | Sets up new projects | Directory structure, config files, initial scaffolding |
| **Planner** | Plans complex work | Multi-step implementation plans with dependencies and risks |
| **TDD Guide** | Enforces test-first development | Makes sure tests are written before implementation, not after |
| **Code Reviewer (General)** | General-purpose review | Works on any language, checks readability, maintainability, patterns |
| **Security Reviewer** | Finds vulnerabilities | OWASP top 10, injection, XSS, auth bypasses, secret exposure |

---

## The Build Pipeline (What Happens When You Say "Build")

```
You: "Build user authentication with Google OAuth"
│
├──► STEP 1: PLAN
│    Architect agent designs: API routes, database schema,
│    auth flow, file structure. Shows you the plan.
│    You approve or adjust.
│
├──► STEP 2: BUILD (parallel)
│    Backend agent: writes auth routes, middleware, tests
│    Frontend agent: writes login page, OAuth callback, tests
│    (Both run TDD — tests first, then implementation)
│    (commit_gate blocks any commit without tests)
│
├──► STEP 3: CODE REVIEW
│    Separate agent reads the code with fresh eyes.
│    Checks for bugs, security issues, edge cases.
│    PASS → continue. NEEDS CHANGES → go back to step 2.
│
├──► STEP 4: QA
│    Autonomous browser agent tests the running app.
│    Clicks every button, tests the login flow, tries
│    invalid inputs, checks mobile/tablet/desktop views.
│    Writes a report. CLEAN → continue. ISSUES → fix and re-test.
│
├──► STEP 5: CTO SIGN-OFF
│    Architecture review agent checks long-term health.
│    APPROVE → continue. BLOCK → back to step 1.
│
├──► STEP 6: DEPLOY
│    DevOps agent: Docker build, server push, Nginx config.
│    Only happens after all gates pass.
│
└──► STEP 7: SAVE
     Session state saved. Project summary updated.
     Bug captures flushed. Ready for next session.
```

---

## The Learning System (How Claude Improves Over Time)

```
Week 1:  Claude writes code → test fails (float rounding error)
         Claude fixes it → test passes
         bug_capture hook auto-records: "float causes rounding in financial code, use Decimal"

Week 2:  Claude starts a new session → reads BUG_CORPUS
         Sees the float bug entry
         Writes Decimal from the start → bug never happens

Week 3:  New bug: API returns null for delisted funds → crash
         Claude fixes it → captured automatically
         BUG_CORPUS now has 2 entries

Week 4:  Claude reads corpus → handles both patterns pre-emptively
         Zero repeat bugs

         ... corpus grows every week ...

Week 12: Claude has 20+ bug patterns memorized
         Code quality improves with every session
         Bugs that used to take hours are prevented in seconds
```

---

## The Memory System (How Claude Remembers Across Sessions)

| File | What It Stores | Survives |
|------|---------------|----------|
| `~/.claude/memory/SESSIONS.md` | What was done each session, decisions made, what's next | Forever |
| `./project/summary.md` (per project) | Full project state — what's built, what's deployed, QA status, pending tasks | Forever |
| `~/.claude/memory/DECISIONS.md` | Permanent architectural rules (e.g. "never use float for money", "single Docker container") | Forever |
| `~/.claude/memory/PATTERNS.md` | Proven code patterns to reuse (API envelope format, config validation, etc.) | Forever |
| `~/.claude/learning/BUG_CORPUS.md` | Bug patterns and their fixes — Claude reads this before writing code | Forever, grows over time |

**What this means:** You can close Claude Code, come back a week later, and Claude knows exactly where you left off, what decisions were made, what bugs to avoid, and what to do next.

---

## Platform Compatibility

| Platform | Works? | Notes |
|----------|--------|-------|
| Claude Code in Terminal (`claude` command) | ✅ Full support | This is the primary platform |
| Claude Code in VS Code | ✅ Full support | Same engine as CLI |
| Claude Code in JetBrains (IntelliJ, WebStorm, etc.) | ✅ Full support | Same engine as CLI |
| claude.ai (browser) | ❌ None of this works | Different product — just a chat interface |
| Claude Desktop app | ❌ None of this works | Different product — just a chat interface |
| Claude mobile app | ❌ None of this works | Different product — just a chat interface |

**Claude Code** = a developer tool with file access, bash execution, and hooks.
**claude.ai / Desktop / Mobile** = a chat interface to talk to Claude. No file access, no hooks, no enforcement.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  JIP ENGINEERING OS — Quick Reference                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  AUTOMATIC (just code normally):                        │
│  • Commits blocked without tests                        │
│  • Code quality checked on every file write             │
│  • Bugs auto-captured for future prevention             │
│  • Session memory saved before context expires          │
│  • Dangerous commands blocked                           │
│  • QA runs after significant commits                    │
│  • Build pipeline tracked and enforced                  │
│                                                         │
│  SAY THESE PHRASES:                                     │
│  • "Build [feature]"     → full pipeline                │
│  • "Retrofit this project" → quality audit              │
│  • "Fix the issues"     → fix from audit report         │
│                                                         │
│  INSTALL:                                               │
│  git clone github.com/nimishshah1989/jip-engineering-os │
│  cd jip-engineering-os && bash install.sh               │
│                                                         │
│  WORKS ON: Claude Code (CLI, VS Code, JetBrains)       │
│  NOT ON:   claude.ai, Desktop app, mobile app           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## GitHub Repository

**https://github.com/nimishshah1989/jip-engineering-os**
