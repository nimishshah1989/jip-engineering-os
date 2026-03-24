# JIP QA Agent
## Autonomous Quality Assurance Loop for All JIP Platforms

Runs on every build. Tests every page, every button, every form, every flow.
Generates a detailed report. Claude Code reads the report and fixes issues.
Loops until the app is clean.

---

## Quick Start (5 minutes)

### Step 1 — Install dependencies

```bash
cd qa_agent
pip install -r requirements.txt
playwright install chromium
```

### Step 2 — Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Add to ~/.zshrc or ~/.bashrc to make permanent
```

### Step 3 — Run against any platform

```bash
# Against local dev server
python run.py --target http://localhost:3000

# Against deployed India Horizon
python run.py --target https://horizon.jslwealth.in

# Against Champion Trader
python run.py --target https://champion.jslwealth.in

# Against Beyond (wealth platform)
python run.py --target https://beyond.jslwealth.in
```

That's it. The agent will:
1. Discover all pages
2. Test every button, form, flow, and visual
3. Write `QA_REPORT.md`
4. Exit with code 1 (fail) if issues found, 0 (pass) if clean

---

## Auto-trigger with Claude Code (the loop)

Add this to your `.claude/settings.json` in each project:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "build|deploy|implement|create|fix",
        "hooks": [
          {
            "type": "command",
            "command": "python /absolute/path/to/qa_agent/run.py --target http://localhost:3000 --report QA_REPORT.md"
          }
        ]
      }
    ]
  }
}
```

Add `CLAUDE_MD_SNIPPET.md` contents to your project's `CLAUDE.md`:

```bash
cat CLAUDE_MD_SNIPPET.md >> /path/to/your/project/CLAUDE.md
```

Now every time Claude Code finishes a task:
1. QA agent runs automatically
2. Report is written to `QA_REPORT.md`
3. Claude Code reads the report before starting the next task
4. Claude Code fixes the issues
5. Build triggers again → QA agent runs again
6. Loop continues until ✅ PASSED

---

## Configuration

Edit `qa_config.yaml` to customise for each platform:

```yaml
pass_conditions:
  max_critical: 0    # Zero critical bugs to pass
  max_major: 0       # Zero major bugs to pass
  max_iterations: 6  # Give up after 6 loop iterations

test_credentials:
  email: "qa@jslwealth.in"  # For testing logged-in flows
  password: "..."
```

---

## Output

### QA_REPORT.md
Structured markdown with:
- Summary table (severity counts vs thresholds)
- Every issue with: description, reproduction steps, expected vs actual, suggested fix, screenshot path
- Pages inventory
- Claude Code instructions

### qa_screenshots/
One folder per iteration. Screenshots named by page and viewport:
```
qa_screenshots/
  iter_1/
    root_desktop.png
    root_mobile.png
    login_desktop.png
    dashboard_tablet.png
    ...
```

---

## Platform-specific configs

Create `qa_config.yaml` in each project root with platform-specific settings.
The agent looks for `qa_config.yaml` in the current directory by default.

```bash
# India Horizon project
cd /path/to/horizon
cp /path/to/qa_agent/qa_config.yaml .
# Edit qa_config.yaml with Horizon-specific settings
python /path/to/qa_agent/run.py --target https://horizon.jslwealth.in

# Champion Trader project  
cd /path/to/champion-trader
cp /path/to/qa_agent/qa_config.yaml .
python /path/to/qa_agent/run.py --target https://champion.jslwealth.in
```

---

## Manual loop (without Claude Code hooks)

If you want to run the loop manually:

```bash
# Iteration 1
python run.py --target http://localhost:3000
# → writes QA_REPORT.md, exits with code 1

# Fix issues manually or with Claude Code
# Then re-run:
python run.py --target http://localhost:3000
# → iteration auto-detected from existing report
# → exits 0 when all thresholds met
```

---

## Extending the agent

Each agent is a standalone class in `agents/`:
- `discovery.py` — add more element types to discover
- `interaction.py` — add more interaction patterns
- `form_fuzzer.py` — add more fuzz payloads
- `flow_walker.py` — add named flows for your specific app
- `visual_inspector.py` — customise the vision prompt

The Claude vision prompt in `visual_inspector.py` is the most powerful lever.
Edit it to focus on issues specific to your platform (e.g. Indian number formatting,
Rupee symbols, lakh/crore notation for JSL Wealth platforms).

---

## Troubleshooting

**"playwright install" fails on EC2**
```bash
sudo apt-get install -y libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
  libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
playwright install chromium
```

**Agent times out on slow pages**
Increase timeouts in `qa_config.yaml`:
```yaml
crawl:
  page_timeout: 30000  # 30 seconds
```

**Too many API calls (Anthropic credits)**
Reduce pages tested by visual inspector:
```python
# In visual_inspector.py, line ~45:
for page_data in site_map["pages"][:5]:  # Reduce from 15 to 5
```
Or reduce viewports to desktop only in `qa_config.yaml`.

---

*JIP QA Agent · Built for Jhaveri Intelligence Platform*
