#!/usr/bin/env node
// Memory Enforcer — Forces session summary writing before context exhaustion
// PostToolUse hook for Bash|Write|Edit
//
// Reads context metrics from the statusline bridge file (same as gsd-context-monitor.js)
// and injects increasingly urgent reminders to write SESSIONS.md.
//
// Thresholds:
//   50% context used: one-time gentle reminder
//   65% context used: every 3 tool calls until SESSIONS.md is written
//   75% context used: every single tool call
//
// Stops nagging once it detects a Write to SESSIONS.md

const fs = require('fs');
const os = require('os');
const path = require('path');

const REMIND_50 = 50;  // remaining_percentage <= 50%
const REMIND_35 = 35;  // remaining_percentage <= 35%
const REMIND_25 = 25;  // remaining_percentage <= 25%

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
    const statePath = path.join(tmpDir, `claude-memory-enforcer-${sessionId}.json`);

    // Load state
    let state = { toolCalls: 0, reminded50: false, reminded65: false, sessionsSaved: false };
    if (fs.existsSync(statePath)) {
      try { state = JSON.parse(fs.readFileSync(statePath, 'utf8')); } catch (e) {}
    }

    state.toolCalls = (state.toolCalls || 0) + 1;

    // Detect if SESSIONS.md was just written
    const toolName = data.tool_name || '';
    const filePath = data.tool_input?.file_path || data.tool_input?.filePath || '';
    if ((toolName === 'Write' || toolName === 'Edit') && filePath.includes('SESSIONS.md')) {
      state.sessionsSaved = true;
      fs.writeFileSync(statePath, JSON.stringify(state));
      process.exit(0);
    }

    // Already saved — stop nagging
    if (state.sessionsSaved) {
      fs.writeFileSync(statePath, JSON.stringify(state));
      process.exit(0);
    }

    // Read context metrics
    const metricsPath = path.join(tmpDir, `claude-ctx-${sessionId}.json`);
    if (!fs.existsSync(metricsPath)) {
      fs.writeFileSync(statePath, JSON.stringify(state));
      process.exit(0);
    }

    const metrics = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
    const remaining = metrics.remaining_percentage;

    // Check if we need to nag
    let message = null;

    if (remaining <= REMIND_25) {
      // Every tool call at critical level
      message = `🚨 MEMORY CRITICAL: Context at ${100 - remaining}% used. ` +
        'You MUST write your session summary to ~/.claude/memory/SESSIONS.md RIGHT NOW. ' +
        'Format: [DATE] [PROJECT] — [what was done] | Decisions: [any] | Bugs: [any] | Next: [exact step]. ' +
        'Also check /tmp/claude_pending_capture.tmp for bug captures.';
    } else if (remaining <= REMIND_35) {
      // Every 3 tool calls
      if (state.toolCalls % 3 === 0) {
        message = `⚠️ MEMORY WARNING: Context at ${100 - remaining}% used. ` +
          'Write your session summary to ~/.claude/memory/SESSIONS.md soon. ' +
          'Format: [DATE] [PROJECT] — [what was done] | Decisions: [any] | Bugs: [any] | Next: [exact step]';
      }
    } else if (remaining <= REMIND_50 && !state.reminded50) {
      state.reminded50 = true;
      message = `💾 Memory reminder: Context at ${100 - remaining}% used. ` +
        'Plan to write your session summary to SESSIONS.md before context fills up.';
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
