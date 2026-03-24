"""
Visual Inspector Agent
Takes screenshots at desktop, tablet, and mobile breakpoints for every page.
Feeds each screenshot to Claude vision with a detailed QA prompt.
Claude identifies: layout breaks, overflow, misalignment, font issues,
colour contrast problems, missing icons, broken images, truncated text.
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import anthropic

# Platform-aware vision prompt — falls back gracefully if import fails
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis.vision_prompt import build_vision_prompt
    _HAS_VISION_PROMPT = True
except ImportError:
    _HAS_VISION_PROMPT = False


class VisualInspectorAgent:
    def __init__(self, base_url: str, config: dict, screenshots_dir: Path):
        self.base_url = base_url
        self.config = config
        self.screenshots_dir = screenshots_dir
        self.screenshot_count = 0
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def run(self, site_map: dict, viewports: list) -> list:
        findings = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for page_data in site_map["pages"][:15]:  # Cap at 15 pages for API cost
                if page_data.get("error"):
                    continue
                for vp in viewports:
                    context = await browser.new_context(
                        viewport={"width": vp["width"], "height": vp["height"]}
                    )
                    page = await context.new_page()
                    try:
                        vp_findings = await self._inspect_page(page, page_data["url"], vp)
                        findings.extend(vp_findings)
                    except Exception as e:
                        findings.append({
                            "type": "visual_inspection_error",
                            "url": page_data["url"],
                            "viewport": vp["name"],
                            "description": f"Screenshot/analysis failed: {str(e)[:150]}",
                            "is_issue": False,
                        })
                    finally:
                        await page.close()
                        await context.close()

            await browser.close()

        return findings

    async def _inspect_page(self, page, url: str, viewport: dict) -> list:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await page.wait_for_timeout(800)  # Let animations settle

        # Screenshot filename
        page_slug = url.replace(self.base_url, "").replace("/", "_").strip("_") or "root"
        screenshot_name = f"{page_slug}_{viewport['name']}.png"
        screenshot_path = self.screenshots_dir / screenshot_name

        await page.screenshot(path=str(screenshot_path), full_page=True)
        self.screenshot_count += 1

        findings = []

        # Check for broken images
        broken_images = await page.evaluate("""() => {
            return Array.from(document.images)
                .filter(img => !img.complete || img.naturalWidth === 0)
                .map(img => img.src)
                .slice(0, 10);
        }""")

        if broken_images:
            findings.append({
                "type": "broken_images",
                "url": url,
                "viewport": viewport["name"],
                "description": f"{len(broken_images)} broken image(s): {', '.join(broken_images[:3])}",
                "is_issue": True,
                "raw_severity": "MAJOR",
                "screenshot": str(screenshot_path),
            })

        # Check for horizontal overflow (especially on mobile)
        has_horizontal_scroll = await page.evaluate("""() => {
            return document.documentElement.scrollWidth > document.documentElement.clientWidth;
        }""")

        if has_horizontal_scroll and viewport["name"] == "mobile":
            findings.append({
                "type": "horizontal_overflow",
                "url": url,
                "viewport": viewport["name"],
                "description": f"Horizontal scroll on {viewport['name']} ({viewport['width']}px) — content overflows viewport",
                "is_issue": True,
                "raw_severity": "MAJOR",
                "screenshot": str(screenshot_path),
            })

        # Claude vision analysis
        vision_findings = await self._analyze_with_claude_vision(screenshot_path, url, viewport)
        findings.extend(vision_findings)

        return findings

    async def _analyze_with_claude_vision(self, screenshot_path: Path, url: str, viewport: dict) -> list:
        """Send screenshot to Claude and ask it to find every visual issue."""
        try:
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return []

        # Use platform-aware prompt if available, else default
        if _HAS_VISION_PROMPT:
            prompt = build_vision_prompt(url, viewport, self.config)
        else:
            prompt = self._default_prompt(url, viewport)

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
            )

            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            issues = []
            if raw.startswith("["):
                parsed = json.loads(raw)
                for item in parsed:
                    issues.append({
                        "type": f"visual_{item.get('type', 'issue')}",
                        "url": url,
                        "viewport": viewport["name"],
                        "description": item.get("description", ""),
                        "element": item.get("element", ""),
                        "is_issue": True,
                        "raw_severity": item.get("severity", "MINOR"),
                        "screenshot": str(screenshot_path),
                        "source": "claude_vision",
                    })
            return issues

        except Exception as e:
            return [{
                "type": "vision_analysis_error",
                "url": url,
                "viewport": viewport["name"],
                "description": f"Claude vision analysis failed: {str(e)[:150]}",
                "is_issue": False,
            }]

    def _default_prompt(self, url: str, viewport: dict) -> str:
        return f"""You are a senior QA engineer reviewing a web application screenshot.

Page URL: {url}
Viewport: {viewport['name']} ({viewport['width']}x{viewport['height']}px)

Identify EVERY visual issue: layout breaks, overlapping elements, truncated text,
broken images, low contrast, form misalignment, horizontal overflow, empty states
without messages, loading spinners where content should be, number formatting issues.

Return ONLY a JSON array. Each item: {{"type": "...", "severity": "CRITICAL|MAJOR|MINOR|COSMETIC",
"description": "...", "element": "..."}}. Empty array if clean."""
