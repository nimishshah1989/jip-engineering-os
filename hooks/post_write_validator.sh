#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# POST WRITE VALIDATOR — Lightweight checks after Write/Edit
# Runs TypeScript type-check only. Pytest moved to bug_capture.sh
# ═══════════════════════════════════════════════════════════════

# TypeScript type check (fast, catches real errors)
if [ -f "package.json" ] && [ -f "tsconfig.json" ]; then
  npx tsc --noEmit 2>&1 | tail -8
fi

exit 0
