"""
Report Generator
Builds the QA_REPORT.md file that Claude Code reads to fix issues.
Designed specifically so Claude Code can:
1. Understand exactly what is broken and where
2. Know the severity and priority order
3. Find the reproduction steps
4. Get a suggested fix for each issue
5. Know when the loop should stop
"""

from datetime import datetime
from pathlib import Path


SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "MAJOR": "🟠",
    "MINOR": "🟡",
    "COSMETIC": "⚪",
}

SEVERITY_ORDER = ["CRITICAL", "MAJOR", "MINOR", "COSMETIC"]


class ReportGenerator:
    def __init__(self, config: dict):
        self.config = config

    def generate(
        self,
        issues: list,
        site_map: dict,
        target_url: str,
        iteration: int,
        severity_counts: dict,
        screenshots_dir: str,
        duration_seconds: int,
    ) -> str:

        pc = self.config["pass_conditions"]
        max_iter = pc.get("max_iterations", 6)
        total_issues = sum(severity_counts.values())
        passed = (
            severity_counts["CRITICAL"] <= pc.get("max_critical", 0)
            and severity_counts["MAJOR"] <= pc.get("max_major", 0)
        )

        lines = []

        # ── HEADER ────────────────────────────────────────────────────────
        lines.append("# QA Report")
        lines.append(f"**Target**: {target_url}  ")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**Iteration**: {iteration} of {max_iter}  ")
        lines.append(f"**Status**: {'✅ PASSED' if passed else '❌ NEEDS FIXES'}  ")
        lines.append("")

        # ── SUMMARY ───────────────────────────────────────────────────────
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Severity | Count | Threshold | Status |")
        lines.append(f"|----------|-------|-----------|--------|")
        lines.append(f"| 🔴 CRITICAL | {severity_counts['CRITICAL']} | ≤ {pc.get('max_critical',0)} | {'✅' if severity_counts['CRITICAL'] <= pc.get('max_critical',0) else '❌'} |")
        lines.append(f"| 🟠 MAJOR    | {severity_counts['MAJOR']} | ≤ {pc.get('max_major',0)} | {'✅' if severity_counts['MAJOR'] <= pc.get('max_major',0) else '❌'} |")
        lines.append(f"| 🟡 MINOR    | {severity_counts['MINOR']} | ≤ {pc.get('max_minor',99)} | {'✅' if severity_counts['MINOR'] <= pc.get('max_minor',99) else '❌'} |")
        lines.append(f"| ⚪ COSMETIC | {severity_counts['COSMETIC']} | — | — |")
        lines.append(f"| **TOTAL**  | **{total_issues}** | | |")
        lines.append("")

        # ── CLAUDE CODE INSTRUCTIONS ───────────────────────────────────────
        lines.append("## Instructions for Claude Code")
        lines.append("")
        if passed:
            lines.append("✅ **All quality thresholds met. No action required.**")
        else:
            lines.append("**Fix all CRITICAL and MAJOR issues below in priority order.**")
            lines.append("After fixing, the QA agent will re-run automatically.")
            lines.append("")
            lines.append("**Fix order:**")
            lines.append("1. All CRITICAL issues first (these block users entirely)")
            lines.append("2. All MAJOR issues (these break important functionality)")
            lines.append("3. MINOR issues if time allows")
            lines.append("")
            lines.append("For each issue: read the description, reproduction steps, and suggested fix.")
            lines.append("Do not mark issues as fixed unless you have actually changed the code.")
        lines.append("")

        # ── COVERAGE ──────────────────────────────────────────────────────
        lines.append("## Test Coverage")
        lines.append("")
        lines.append(f"- Pages tested: {len(site_map.get('pages', []))}")
        lines.append(f"- Forms fuzzed: {site_map.get('total_forms', 0)}")
        lines.append(f"- Buttons tested: {site_map.get('total_buttons', 0)}")
        lines.append(f"- Input fields: {site_map.get('total_inputs', 0)}")
        lines.append(f"- Flows walked: {len(site_map.get('flows', []))}")
        lines.append(f"- Screenshots taken: see `{screenshots_dir}/`")
        lines.append("")

        # ── ISSUES BY SEVERITY ────────────────────────────────────────────
        for severity in SEVERITY_ORDER:
            sev_issues = [i for i in issues if i.get("severity") == severity]
            if not sev_issues:
                continue

            emoji = SEVERITY_EMOJI[severity]
            lines.append(f"---")
            lines.append(f"## {emoji} {severity} Issues ({len(sev_issues)})")
            lines.append("")

            for issue in sev_issues:
                lines.append(f"### {issue.get('id', '?')} — {issue.get('title', 'Issue')}")
                lines.append("")
                lines.append(f"**Page**: `{issue.get('page', 'unknown')}`  ")
                lines.append(f"**Viewport**: {issue.get('viewport', 'all')}  ")
                lines.append(f"**Type**: `{issue.get('type', 'unknown')}`  ")
                lines.append("")
                lines.append(f"**Description**:  ")
                lines.append(f"{issue.get('description', '')}")
                lines.append("")

                repro = issue.get("reproduction_steps", [])
                if repro:
                    lines.append("**Reproduction steps**:")
                    for step in repro:
                        lines.append(f"1. {step}")
                    lines.append("")

                expected = issue.get("expected", "")
                actual = issue.get("actual", "")
                if expected:
                    lines.append(f"**Expected**: {expected}  ")
                if actual:
                    lines.append(f"**Actual**: {actual}  ")
                if expected or actual:
                    lines.append("")

                fix = issue.get("suggested_fix", "")
                if fix:
                    lines.append(f"**Suggested fix**:  ")
                    lines.append(f"{fix}")
                    lines.append("")

                screenshot = issue.get("screenshot")
                if screenshot and Path(screenshot).exists():
                    lines.append(f"**Screenshot**: `{screenshot}`  ")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # ── PAGES INVENTORY ───────────────────────────────────────────────
        lines.append("## Pages Discovered")
        lines.append("")
        for page in site_map.get("pages", [])[:30]:
            url = page.get("url", "")
            err = page.get("error", "")
            status = f"❌ ERROR: {err[:60]}" if err else "✓"
            lines.append(f"- `{url}` — {status}")
        lines.append("")

        # ── FOOTER ────────────────────────────────────────────────────────
        lines.append("---")
        lines.append(f"*Generated by JIP QA Agent · Iteration {iteration}/{max_iter}*")
        if not passed:
            lines.append(f"*Next step: Claude Code fixes issues → re-build → QA agent re-runs*")

        return "\n".join(lines)
