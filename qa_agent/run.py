#!/usr/bin/env python3
"""
JIP QA Agent — Autonomous Quality Assurance Loop
Runs on every build. Tests everything. Reports everything. Loops until clean.

Usage:
    python run.py --target http://localhost:3000
    python run.py --target https://horizon.jslwealth.in --config qa_config.yaml
    python run.py --target http://localhost:3000 --iteration 2 --report QA_REPORT.md
"""

import argparse
import asyncio
import json
import os
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path

from agents.discovery import DiscoveryAgent
from agents.interaction import InteractionAgent
from agents.form_fuzzer import FormFuzzerAgent
from agents.flow_walker import FlowWalkerAgent
from agents.visual_inspector import VisualInspectorAgent
from analysis.claude_analyzer import ClaudeAnalyzer
from report.generator import ReportGenerator

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         JIP QA AGENT — Autonomous Quality Loop              ║
║         Tests every button. Every form. Every flow.         ║
╚══════════════════════════════════════════════════════════════╝
"""


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def check_existing_report(report_path: str) -> int:
    """Read current iteration from existing report if it exists."""
    if not os.path.exists(report_path):
        return 1
    with open(report_path) as f:
        content = f.read()
    for line in content.splitlines():
        if line.startswith("## Iteration:"):
            try:
                return int(line.split(":")[1].strip().split(" ")[0]) + 1
            except Exception:
                pass
    return 1


async def run_qa_loop(target_url: str, config: dict, report_path: str, iteration: int):
    print(BANNER)
    print(f"  Target   : {target_url}")
    print(f"  Iteration: {iteration} / {config['pass_conditions']['max_iterations']}")
    print(f"  Report   : {report_path}")
    print(f"  Started  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    screenshots_dir = Path("qa_screenshots") / f"iter_{iteration}"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    all_findings = []
    phase_results = {}

    # ─── PHASE 1: DISCOVERY ────────────────────────────────────────────────
    print("━" * 60)
    print("PHASE 1 — Discovery: mapping all pages and interactive elements")
    print("━" * 60)

    discovery = DiscoveryAgent(target_url, config)
    site_map = await discovery.run()

    print(f"  ✓ Pages found       : {len(site_map['pages'])}")
    print(f"  ✓ Forms found       : {site_map['total_forms']}")
    print(f"  ✓ Buttons found     : {site_map['total_buttons']}")
    print(f"  ✓ Input fields      : {site_map['total_inputs']}")
    print(f"  ✓ User flows mapped : {len(site_map.get('flows', []))}")
    print()

    phase_results["discovery"] = site_map

    # ─── PHASE 2: INTERACTION TESTING ──────────────────────────────────────
    print("━" * 60)
    print("PHASE 2 — Interaction: clicking every button, link, and control")
    print("━" * 60)

    interaction_agent = InteractionAgent(target_url, config, screenshots_dir)
    interaction_findings = await interaction_agent.run(site_map)
    all_findings.extend(interaction_findings)
    print(f"  ✓ Elements tested   : {len(interaction_findings)}")
    print(f"  ✓ Issues detected   : {sum(1 for f in interaction_findings if f.get('is_issue'))}")
    print()

    # ─── PHASE 2B: FORM FUZZING ────────────────────────────────────────────
    print("━" * 60)
    print("PHASE 2B — Form fuzzer: valid, invalid, empty, and edge case inputs")
    print("━" * 60)

    fuzzer = FormFuzzerAgent(target_url, config, screenshots_dir)
    fuzz_findings = await fuzzer.run(site_map)
    all_findings.extend(fuzz_findings)
    print(f"  ✓ Forms tested      : {site_map['total_forms']}")
    print(f"  ✓ Test combinations : {len(fuzz_findings)}")
    print(f"  ✓ Issues detected   : {sum(1 for f in fuzz_findings if f.get('is_issue'))}")
    print()

    # ─── PHASE 2C: FLOW WALKING ────────────────────────────────────────────
    print("━" * 60)
    print("PHASE 2C — Flow walker: all user journeys, happy + error paths")
    print("━" * 60)

    flow_walker = FlowWalkerAgent(target_url, config, screenshots_dir)
    flow_findings = await flow_walker.run(site_map)
    all_findings.extend(flow_findings)
    print(f"  ✓ Flows walked      : {len(site_map.get('flows', []))}")
    print(f"  ✓ Issues detected   : {sum(1 for f in flow_findings if f.get('is_issue'))}")
    print()

    # ─── PHASE 2D: VISUAL INSPECTION ───────────────────────────────────────
    print("━" * 60)
    print("PHASE 2D — Visual inspector: screenshots + Claude vision analysis")
    print("━" * 60)

    viewports = config.get("viewports", [
        {"name": "desktop", "width": 1440, "height": 900},
        {"name": "tablet",  "width": 768,  "height": 1024},
        {"name": "mobile",  "width": 375,  "height": 812},
    ])

    inspector = VisualInspectorAgent(target_url, config, screenshots_dir)
    visual_findings = await inspector.run(site_map, viewports)
    all_findings.extend(visual_findings)
    print(f"  ✓ Screenshots taken : {inspector.screenshot_count}")
    print(f"  ✓ Visual issues     : {sum(1 for f in visual_findings if f.get('is_issue'))}")
    print()

    # ─── PHASE 3: CLAUDE ANALYSIS ──────────────────────────────────────────
    print("━" * 60)
    print("PHASE 3 — Claude analysis: classifying and prioritising all findings")
    print("━" * 60)

    analyzer = ClaudeAnalyzer(config)
    analyzed_issues = await analyzer.analyze(all_findings, site_map, target_url)

    severity_counts = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0, "COSMETIC": 0}
    for issue in analyzed_issues:
        sev = issue.get("severity", "MINOR")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    print(f"  ✓ CRITICAL  : {severity_counts['CRITICAL']}")
    print(f"  ✓ MAJOR     : {severity_counts['MAJOR']}")
    print(f"  ✓ MINOR     : {severity_counts['MINOR']}")
    print(f"  ✓ COSMETIC  : {severity_counts['COSMETIC']}")
    print()

    # ─── PHASE 4: REPORT GENERATION ────────────────────────────────────────
    print("━" * 60)
    print("PHASE 4 — Writing QA_REPORT.md for Claude Code")
    print("━" * 60)

    generator = ReportGenerator(config)
    report_content = generator.generate(
        issues=analyzed_issues,
        site_map=site_map,
        target_url=target_url,
        iteration=iteration,
        severity_counts=severity_counts,
        screenshots_dir=str(screenshots_dir),
        duration_seconds=int(time.time()),
    )

    with open(report_path, "w") as f:
        f.write(report_content)

    print(f"  ✓ Report written to : {report_path}")
    print()

    # ─── QUALITY GATE ──────────────────────────────────────────────────────
    pc = config["pass_conditions"]
    passed = (
        severity_counts["CRITICAL"] <= pc.get("max_critical", 0)
        and severity_counts["MAJOR"] <= pc.get("max_major", 0)
        and severity_counts["MINOR"] <= pc.get("max_minor", 99)
    )

    print("━" * 60)
    if passed:
        print("✅  QUALITY GATE PASSED — build is clean")
        print("━" * 60)
        sys.exit(0)
    elif iteration >= pc.get("max_iterations", 6):
        print(f"⚠️   MAX ITERATIONS ({pc['max_iterations']}) REACHED — exiting loop")
        print("    Review QA_REPORT.md manually.")
        print("━" * 60)
        sys.exit(2)
    else:
        print(f"❌  QUALITY GATE FAILED — {severity_counts['CRITICAL']} critical, {severity_counts['MAJOR']} major")
        print("    Claude Code will read QA_REPORT.md and fix issues.")
        print("    Hook will re-trigger after next build.")
        print("━" * 60)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="JIP QA Agent")
    parser.add_argument("--target", required=True, help="URL to test (e.g. http://localhost:3000)")
    parser.add_argument("--config", default="qa_config.yaml", help="Config file path")
    parser.add_argument("--report", default="QA_REPORT.md", help="Output report path")
    parser.add_argument("--iteration", type=int, default=None, help="Iteration number (auto-detected if omitted)")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.iteration is not None:
        iteration = args.iteration
    else:
        iteration = check_existing_report(args.report)

    asyncio.run(run_qa_loop(args.target, config, args.report, iteration))


if __name__ == "__main__":
    main()
