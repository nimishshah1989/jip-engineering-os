#!/usr/bin/env node
// QA Checkpoint — Reminds about QA after meaningful milestones
// PostToolUse hook for Bash
//
// Tracks file edits and commits across the session.
// Injects QA reminders when:
//   - A commit is made after 5+ files changed
//   - 20+ file edits without any test execution
//   - Tests pass after a fix (the "green" moment)

const fs = require('fs');
const os = require('os');
const path = require('path');

let input = '';
const stdinTimeout = setTimeout(() => process.exit(0), 5000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const sessionId = data.session_id;
    if (!sessionId) process.exit(0);

    const tmpDir = os.tmpdir();
    const statePath = path.join(tmpDir, `claude-qa-checkpoint-${sessionId}.json`);
    const cwd = data.cwd || process.cwd();

    // Load state
    let state = { filesChanged: 0, testsRun: 0, lastReminder: 0, commitsTracked: 0 };
    if (fs.existsSync(statePath)) {
      try { state = JSON.parse(fs.readFileSync(statePath, 'utf8')); } catch (e) {}
    }

    const cmd = data.tool_input?.command || '';
    const toolName = data.tool_name || '';

    // Track file changes (Write/Edit calls get routed here too via the matcher in settings)
    if (toolName === 'Write' || toolName === 'Edit' || toolName === 'MultiEdit') {
      const fp = data.tool_input?.file_path || data.tool_input?.filePath || '';
      if (fp.match(/\.(py|ts|tsx|js|jsx|css|html)$/)) {
        state.filesChanged = (state.filesChanged || 0) + 1;
      }
    }

    // Track test execution
    if (cmd.match(/pytest|npm\s+test|npx\s+jest|yarn\s+test|cargo\s+test|vitest/)) {
      state.testsRun = (state.testsRun || 0) + 1;
      state.lastTestRun = state.filesChanged;
    }

    let message = null;

    // Check: commit after many file changes
    if (cmd.match(/git\s+commit/)) {
      state.commitsTracked = (state.commitsTracked || 0) + 1;
      const filesSinceReminder = state.filesChanged - (state.lastReminder || 0);

      if (filesSinceReminder >= 5 && fs.existsSync(path.join(cwd, 'qa_config.yaml'))) {
        message = `📋 QA CHECKPOINT: ${state.filesChanged} files changed, ${state.commitsTracked} commits this session. ` +
          'Consider running QA: python ~/.claude/qa_agent/run.py --target [url]. ' +
          'Check QA_REPORT.md for CRITICAL/MAJOR issues.';
        state.lastReminder = state.filesChanged;
      }
    }

    // Check: too many edits without tests
    const editsSinceTest = state.filesChanged - (state.lastTestRun || 0);
    if (editsSinceTest >= 20 && !message) {
      message = `⚠️ TEST GAP: ${editsSinceTest} file edits since last test run. ` +
        'Run pytest/npm test before continuing. TDD means test FIRST, not test never.';
      state.lastTestRun = state.filesChanged; // reset to avoid spamming
    }

    fs.writeFileSync(statePath, JSON.stringify(state));

    if (message) {
      const output = {
        hookSpecificOutput: {
          hookEventName: "PostToolUse",
          additionalContext: message
        }
      };
      process.stdout.write(JSON.stringify(output));
    }
  } catch (e) {
    process.exit(0);
  }
});
