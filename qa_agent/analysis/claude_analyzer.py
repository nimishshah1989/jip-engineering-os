"""
Claude Analyzer
Takes all raw findings from all 4 agents and runs them through Claude
to produce a clean, deduplicated, severity-classified issue list
with suggested fixes for each one.
"""

import json
import os
import anthropic


ANALYSIS_SYSTEM_PROMPT = """You are a senior QA engineer and product quality lead.
You receive raw test findings from an automated QA system and must:
1. Deduplicate similar issues (merge issues that describe the same root problem)
2. Classify each issue with the correct severity
3. Write a clear, actionable description
4. Suggest a specific fix
5. Add reproduction steps

Severity definitions:
- CRITICAL: Blocks core functionality (can't login, app crashes, data loss, blank page)
- MAJOR: Significant feature broken or unusable (form doesn't submit, wrong data shown, mobile layout broken)
- MINOR: Feature works but has UX issues (poor error messages, validation gaps, styling inconsistency)
- COSMETIC: Visual polish only (minor spacing, font inconsistency, icon size)

Return ONLY a JSON array of issues. Each issue must have exactly these fields:
{
  "id": "ISSUE-001",
  "severity": "CRITICAL|MAJOR|MINOR|COSMETIC",
  "type": "short_snake_case_category",
  "page": "the URL or page name",
  "viewport": "desktop|tablet|mobile|all",
  "title": "One line issue title (max 80 chars)",
  "description": "Full description of what is wrong and where",
  "reproduction_steps": ["Step 1", "Step 2", "Step 3"],
  "expected": "What should happen",
  "actual": "What actually happens",
  "suggested_fix": "Specific code/design suggestion for fixing this",
  "screenshot": "path/to/screenshot.png or null"
}"""


class ClaudeAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def analyze(self, findings: list, site_map: dict, target_url: str) -> list:
        """Send all findings to Claude for analysis, deduplication, and classification."""

        # Filter to only issues
        raw_issues = [f for f in findings if f.get("is_issue")]

        if not raw_issues:
            return []

        # Chunk if too many findings (API context limits)
        chunks = [raw_issues[i:i+40] for i in range(0, len(raw_issues), 40)]
        all_analyzed = []
        issue_counter = 1

        for chunk_idx, chunk in enumerate(chunks):
            analyzed = await self._analyze_chunk(chunk, target_url, issue_counter)
            all_analyzed.extend(analyzed)
            issue_counter += len(analyzed)

        # Final dedup pass if multiple chunks
        if len(chunks) > 1:
            all_analyzed = await self._dedup_pass(all_analyzed, target_url)

        return all_analyzed

    async def _analyze_chunk(self, findings: list, target_url: str, start_idx: int) -> list:
        findings_text = json.dumps(findings, indent=2, default=str)

        prompt = f"""Target application: {target_url}

Raw QA findings to analyze:
{findings_text}

Analyze these findings. Deduplicate where the same issue appears multiple times.
Classify severity accurately. Add reproduction steps and fix suggestions.
Number issues starting from ISSUE-{start_idx:03d}.

Return ONLY the JSON array."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            if raw.startswith("["):
                return json.loads(raw)
            return []

        except Exception as e:
            # Return findings as-is with basic classification
            return [self._basic_classify(f, i + start_idx) for i, f in enumerate(findings)]

    async def _dedup_pass(self, issues: list, target_url: str) -> list:
        """Final deduplication pass across all chunks."""
        if len(issues) <= 5:
            return issues

        issues_text = json.dumps(issues, indent=2, default=str)
        prompt = f"""These issues were found across multiple analysis chunks for {target_url}.
Some may be duplicates. Merge any duplicate issues, keeping the most complete description.
Renumber all issues from ISSUE-001.
Return ONLY the deduplicated JSON array."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt + "\n\n" + issues_text}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
            if raw.startswith("["):
                return json.loads(raw.strip())
        except Exception:
            pass

        return issues

    def _basic_classify(self, finding: dict, idx: int) -> dict:
        """Fallback basic classification if Claude API fails."""
        raw_sev = finding.get("raw_severity", "MINOR")
        return {
            "id": f"ISSUE-{idx:03d}",
            "severity": raw_sev if raw_sev in ("CRITICAL", "MAJOR", "MINOR", "COSMETIC") else "MINOR",
            "type": finding.get("type", "unknown"),
            "page": finding.get("url", "unknown"),
            "viewport": finding.get("viewport", "all"),
            "title": finding.get("description", "Issue detected")[:80],
            "description": finding.get("description", ""),
            "reproduction_steps": ["Navigate to the page", "Observe the issue"],
            "expected": "Feature works correctly",
            "actual": finding.get("description", ""),
            "suggested_fix": "Investigate and fix the root cause",
            "screenshot": finding.get("screenshot"),
        }
