#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════
// BUILD CYCLE ENFORCER — Tracks and enforces the mandatory build cycle
// PostToolUse hook for Agent|Bash|Write|Edit
//
// Tracks which agents have been invoked this session and warns
// when the build cycle is being violated:
//
// architect → backend/frontend → code-review → qa → verifier → cto → devops
//
// Also detects when code is being written without a plan,
// or when deploys are attempted without review.
// ═══════════════════════════════════════════════════════════════

const fs = require('fs');
const os = require('os');
const path = require('path');

const CYCLE_ORDER = [
  'jip-architect',
  'jip-backend|jip-frontend',
  'jip-code-review',
  'jip-qa',
  'jip-verifier',
  'jip-cto',
  'jip-devops'
];

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
    const statePath = path.join(tmpDir, `claude-build-cycle-${sessionId}.json`);
    const cwd = data.cwd || process.cwd();

    // Only track in git repos (actual projects)
    if (!fs.existsSync(path.join(cwd, '.git'))) process.exit(0);

    // Load state
    let state = {
      agentsInvoked: [],
      codeWritten: false,
      planExists: false,
      filesWritten: 0,
      deployAttempted: false,
      warned: {}
    };
    if (fs.existsSync(statePath)) {
      try { state = JSON.parse(fs.readFileSync(statePath, 'utf8')); } catch (e) {}
    }

    const cmd = data.tool_input?.command || '';
    const toolName = data.tool_name || '';
    const filePath = data.tool_input?.file_path || data.tool_input?.filePath || '';

    // Track agent invocations (from Agent tool or subagent_type)
    const agentType = data.tool_input?.subagent_type || '';
    const agentPrompt = (data.tool_input?.prompt || '').toLowerCase();

    // Detect agent references
    for (const agent of ['jip-architect', 'jip-backend', 'jip-frontend', 'jip-code-review', 'jip-qa', 'jip-verifier', 'jip-cto', 'jip-devops', 'jip-memory-keeper']) {
      if (agentType.includes(agent) || agentPrompt.includes(agent) || cmd.includes(agent)) {
        if (!state.agentsInvoked.includes(agent)) {
          state.agentsInvoked.push(agent);
        }
      }
    }

    // Track code writing
    if ((toolName === 'Write' || toolName === 'Edit') && filePath.match(/\.(py|ts|tsx|js|jsx)$/)) {
      state.codeWritten = true;
      state.filesWritten = (state.filesWritten || 0) + 1;
    }

    // Check for plan files
    if (fs.existsSync(path.join(cwd, 'project', 'PLAN.md')) ||
        fs.existsSync(path.join(cwd, '.planning', 'current-phase')) ||
        state.agentsInvoked.includes('jip-architect')) {
      state.planExists = true;
    }

    // Detect deploy attempts
    if (cmd.match(/docker.*(build|push|compose.*up)|ssh.*ubuntu@|deploy|jip-devops/)) {
      state.deployAttempted = true;
    }

    let message = null;

    // RULE 1: Code without a plan (after 5+ files)
    if (state.codeWritten && !state.planExists && state.filesWritten >= 5 && !state.warned.noPlan) {
      message = '⚠️ BUILD CYCLE: You\'ve written ' + state.filesWritten + ' code files without a plan. ' +
        'The mandatory cycle requires jip-architect to create a plan FIRST. ' +
        'Either invoke the planner agent now or acknowledge this is a small fix that doesn\'t need a plan.';
      state.warned.noPlan = true;
    }

    // RULE 2: Deploy without code review
    if (state.deployAttempted && !state.agentsInvoked.includes('jip-code-review') && !state.warned.noReview) {
      message = '🚫 BUILD CYCLE VIOLATION: Deploy attempted without jip-code-review. ' +
        'The mandatory cycle requires: code → jip-code-review → jip-qa → jip-cto → THEN deploy. ' +
        'Run code review first.';
      state.warned.noReview = true;
    }

    // RULE 3: Deploy without CTO sign-off
    if (state.deployAttempted && !state.agentsInvoked.includes('jip-cto') && !state.warned.noCTO) {
      message = '🚫 BUILD CYCLE VIOLATION: Deploy attempted without jip-cto sign-off. ' +
        'No deploy happens without CTO APPROVE verdict.';
      state.warned.noCTO = true;
    }

    // RULE 4: After 15+ files, remind about code review
    if (state.filesWritten >= 15 && !state.agentsInvoked.includes('jip-code-review') && !state.warned.reviewReminder) {
      message = '📋 BUILD CYCLE: ' + state.filesWritten + ' files written. Time for jip-code-review. ' +
        'A fresh-eyes review catches bugs you\'re blind to after writing the code.';
      state.warned.reviewReminder = true;
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
