"""
QA Dashboard Server
Serves a live HTML dashboard that reads QA_REPORT.md and auto-refreshes.
Run with: python dashboard/serve.py
Or via the qa command: qa dashboard

Visit: http://localhost:8765
"""

import http.server
import json
import os
import re
import socketserver
import threading
import time
import webbrowser
from pathlib import Path

PORT = 8765
REPORT_PATH = "QA_REPORT.md"
SCREENSHOTS_DIR = "qa_screenshots"


def parse_report(path: str) -> dict:
    """Parse QA_REPORT.md into structured data for the dashboard."""
    if not os.path.exists(path):
        return {"found": False}

    with open(path) as f:
        content = f.read()

    result = {
        "found": True,
        "raw": content,
        "target": "",
        "generated": "",
        "iteration": "",
        "status": "UNKNOWN",
        "severity_counts": {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0, "COSMETIC": 0},
        "issues": [],
        "pages": [],
    }

    for line in content.splitlines():
        if line.startswith("**Target**:"):
            result["target"] = line.replace("**Target**:", "").strip().rstrip("  ")
        elif line.startswith("**Generated**:"):
            result["generated"] = line.replace("**Generated**:", "").strip().rstrip("  ")
        elif line.startswith("**Iteration**:"):
            result["iteration"] = line.replace("**Iteration**:", "").strip().rstrip("  ")
        elif line.startswith("**Status**:"):
            result["status"] = "PASSED" if "PASSED" in line else "FAILED"

    # Parse severity counts from table
    for line in content.splitlines():
        for sev in ("CRITICAL", "MAJOR", "MINOR", "COSMETIC"):
            if f"| {sev}" in line or f"| 🔴 {sev}" in line or f"| 🟠 {sev}" in line or f"| 🟡 {sev}" in line or f"| ⚪ {sev}" in line:
                match = re.search(r"\|\s*\w+\s*\|\s*(\d+)", line)
                if match:
                    result["severity_counts"][sev] = int(match.group(1))

    # Parse issues
    current_issue = None
    for line in content.splitlines():
        if re.match(r"^### (ISSUE-\d+)", line):
            if current_issue:
                result["issues"].append(current_issue)
            issue_id = re.search(r"(ISSUE-\d+)", line).group(1)
            title = re.sub(r"^### ISSUE-\d+ — ", "", line).strip()
            current_issue = {"id": issue_id, "title": title, "severity": "MINOR", "page": "", "description": "", "fix": ""}
        elif current_issue:
            if line.startswith("**Page**:"):
                current_issue["page"] = line.replace("**Page**:", "").strip().strip("`").rstrip("  ")
            elif line.startswith("**Description**:"):
                pass
            elif line.startswith("**Suggested fix**:"):
                pass
            elif current_issue.get("_next_desc"):
                current_issue["description"] = line.strip()
                current_issue["_next_desc"] = False
            elif current_issue.get("_next_fix"):
                current_issue["fix"] = line.strip()
                current_issue["_next_fix"] = False

    if current_issue:
        result["issues"].append(current_issue)

    # Assign severity from section context
    current_sev = "MINOR"
    for line in content.splitlines():
        for sev in ("CRITICAL", "MAJOR", "MINOR", "COSMETIC"):
            if f"## " in line and sev in line:
                current_sev = sev
        m = re.match(r"^### (ISSUE-\d+)", line)
        if m:
            iid = m.group(1)
            for issue in result["issues"]:
                if issue["id"] == iid:
                    issue["severity"] = current_sev

    return result


def build_html(data: dict) -> str:
    if not data.get("found"):
        return _no_report_html()

    status = data["status"]
    sc = data["severity_counts"]
    total = sum(sc.values())
    issues = data["issues"]

    status_color = "#16a34a" if status == "PASSED" else "#dc2626"
    status_bg = "#f0fdf4" if status == "PASSED" else "#fef2f2"
    status_icon = "✅" if status == "PASSED" else "❌"

    issues_html = ""
    for sev in ("CRITICAL", "MAJOR", "MINOR", "COSMETIC"):
        sev_issues = [i for i in issues if i.get("severity") == sev]
        if not sev_issues:
            continue
        colors = {
            "CRITICAL": ("#dc2626", "#fef2f2", "🔴"),
            "MAJOR": ("#ea580c", "#fff7ed", "🟠"),
            "MINOR": ("#ca8a04", "#fefce8", "🟡"),
            "COSMETIC": ("#6b7280", "#f9fafb", "⚪"),
        }
        c, bg, emoji = colors[sev]
        issues_html += f'<div class="sev-group"><h3 style="color:{c}">{emoji} {sev} ({len(sev_issues)})</h3>'
        for issue in sev_issues:
            issues_html += f"""
<div class="issue-card" style="border-left:4px solid {c}">
  <div class="issue-header">
    <span class="issue-id" style="color:{c}">{issue['id']}</span>
    <span class="issue-title">{issue['title']}</span>
  </div>
  <div class="issue-meta">
    <span class="tag">📄 {issue.get('page','') or 'unknown'}</span>
  </div>
  {f'<p class="issue-desc">{issue["description"]}</p>' if issue.get("description") else ''}
  {f'<div class="fix-hint">💡 {issue["fix"]}</div>' if issue.get("fix") else ''}
</div>"""
        issues_html += "</div>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JIP QA Dashboard</title>
<meta http-equiv="refresh" content="15">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; font-size: 14px; }}
  .topbar {{ background: #0f172a; color: #e2e8f0; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; }}
  .topbar h1 {{ font-size: 16px; font-weight: 600; letter-spacing: 0.3px; }}
  .topbar .meta {{ font-size: 12px; color: #94a3b8; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px; }}
  .status-banner {{ border-radius: 10px; padding: 20px 24px; margin-bottom: 24px; background: {status_bg}; border: 1px solid {"#bbf7d0" if status == "PASSED" else "#fecaca"}; display: flex; align-items: center; gap: 16px; }}
  .status-icon {{ font-size: 32px; }}
  .status-text h2 {{ font-size: 20px; font-weight: 700; color: {status_color}; }}
  .status-text p {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
  .card {{ background: white; border-radius: 8px; padding: 16px 20px; border: 1px solid #e2e8f0; }}
  .card .num {{ font-size: 32px; font-weight: 700; line-height: 1; }}
  .card .label {{ font-size: 12px; color: #64748b; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .card.critical .num {{ color: #dc2626; }}
  .card.major .num {{ color: #ea580c; }}
  .card.minor .num {{ color: #ca8a04; }}
  .card.cosmetic .num {{ color: #6b7280; }}
  .sev-group {{ margin-bottom: 24px; }}
  .sev-group h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }}
  .issue-card {{ background: white; border-radius: 8px; padding: 16px 20px; margin-bottom: 10px; border: 1px solid #e2e8f0; }}
  .issue-header {{ display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; }}
  .issue-id {{ font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; background: #f1f5f9; white-space: nowrap; }}
  .issue-title {{ font-size: 14px; font-weight: 600; color: #0f172a; line-height: 1.4; }}
  .issue-meta {{ display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
  .tag {{ font-size: 11px; background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 20px; }}
  .issue-desc {{ font-size: 13px; color: #475569; line-height: 1.6; margin-bottom: 8px; }}
  .fix-hint {{ font-size: 12px; color: #166534; background: #f0fdf4; border-radius: 6px; padding: 8px 12px; border-left: 3px solid #16a34a; }}
  .no-issues {{ background: white; border-radius: 8px; padding: 40px; text-align: center; color: #16a34a; font-size: 16px; border: 1px solid #bbf7d0; }}
  .refresh-note {{ text-align: center; color: #94a3b8; font-size: 11px; margin-top: 24px; }}
  @media (max-width: 600px) {{ .cards {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
</head>
<body>
<div class="topbar">
  <h1>JIP QA Dashboard</h1>
  <div class="meta">{data.get('target','')} · {data.get('generated','')} · Iteration {data.get('iteration','')}</div>
</div>
<div class="container">
  <div class="status-banner">
    <div class="status-icon">{status_icon}</div>
    <div class="status-text">
      <h2>Quality Gate {status}</h2>
      <p>{total} total issues found · Auto-refreshes every 15 seconds</p>
    </div>
  </div>
  <div class="cards">
    <div class="card critical"><div class="num">{sc['CRITICAL']}</div><div class="label">🔴 Critical</div></div>
    <div class="card major"><div class="num">{sc['MAJOR']}</div><div class="label">🟠 Major</div></div>
    <div class="card minor"><div class="num">{sc['MINOR']}</div><div class="label">🟡 Minor</div></div>
    <div class="card cosmetic"><div class="num">{sc['COSMETIC']}</div><div class="label">⚪ Cosmetic</div></div>
  </div>
  {issues_html if issues_html else '<div class="no-issues">✅ No issues found — all tests passed</div>'}
  <div class="refresh-note">Auto-refreshing every 15 seconds · Open QA_REPORT.md for full details</div>
</div>
</body>
</html>"""


def _no_report_html() -> str:
    return """<!DOCTYPE html><html><body style="font-family:sans-serif;padding:40px;text-align:center;color:#64748b">
<h2>No QA_REPORT.md found</h2>
<p>Run the QA agent first: <code>qa --target http://localhost:3000</code></p>
<meta http-equiv="refresh" content="10">
</body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/report":
            data = parse_report(REPORT_PATH)
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/qa_screenshots/"):
            # Serve screenshot images
            file_path = self.path.lstrip("/")
            if os.path.exists(file_path) and file_path.endswith(".png"):
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            data = parse_report(REPORT_PATH)
            html = build_html(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

    def log_message(self, format, *args):
        pass  # Suppress request logs


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    url = f"http://localhost:{port}"

    print(f"\n  QA Dashboard running at {url}")
    print(f"  Reading: {os.path.abspath(REPORT_PATH)}")
    print(f"  Auto-refreshes every 15 seconds")
    print(f"  Ctrl+C to stop\n")

    # Open browser after a short delay
    def open_browser():
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Dashboard stopped.")
