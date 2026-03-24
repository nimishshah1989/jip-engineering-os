# QA Agent Rules — Add this section to your project CLAUDE.md

## Autonomous QA Loop

**MANDATORY**: After completing any build, feature implementation, or bug fix task:

1. **Check for QA_REPORT.md** in the project root.
2. If it exists and contains CRITICAL or MAJOR issues:
   - Read the full report before writing any new code
   - Fix ALL CRITICAL issues first (they block users)
   - Fix ALL MAJOR issues second
   - Follow the "Suggested fix" in each issue
   - Do not mark issues as fixed unless code has actually changed
3. After fixing, run the build/deploy command — the QA agent will trigger automatically.
4. Repeat until QA_REPORT.md shows ✅ PASSED status.

**Never skip the QA report.** If QA_REPORT.md exists, it takes priority over any new feature work.

## QA Report Location

- Report: `QA_REPORT.md` (project root)  
- Screenshots: `qa_screenshots/iter_N/` (one folder per iteration)

## Issue Priority Order

1. 🔴 CRITICAL — fix immediately, nothing else matters
2. 🟠 MAJOR — fix before any new features
3. 🟡 MINOR — fix if in scope of current task
4. ⚪ COSMETIC — backlog, low priority
