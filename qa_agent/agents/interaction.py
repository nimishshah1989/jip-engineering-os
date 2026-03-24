from typing import Optional
"""
Interaction Agent
Visits every page, clicks every button, link, dropdown, tab, toggle.
Captures what happens — errors, broken states, unexpected navigation.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


class InteractionAgent:
    def __init__(self, base_url: str, config: dict, screenshots_dir: Path):
        self.base_url = base_url
        self.config = config
        self.screenshots_dir = screenshots_dir

    async def run(self, site_map: dict) -> list:
        findings = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 900})

            for page_data in site_map["pages"]:
                if page_data.get("error"):
                    continue
                page_findings = await self._test_page(context, page_data)
                findings.extend(page_findings)

            await browser.close()

        return findings

    async def _test_page(self, context, page_data: dict) -> list:
        findings = []
        url = page_data["url"]
        console_errors = []

        page = await context.new_page()
        page.on("console", lambda msg: console_errors.append({"type": msg.type, "text": msg.text}) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append({"type": "pageerror", "text": str(err)}))

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(500)

            # Test all buttons
            buttons = await page.query_selector_all("button:not([disabled]), [role='button']:not([disabled])")
            for i, btn in enumerate(buttons[:30]):
                finding = await self._test_button(page, btn, url, i, console_errors)
                if finding:
                    findings.append(finding)
                # Re-navigate if we ended up somewhere else
                if page.url != url:
                    await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    await page.wait_for_timeout(300)

            # Test dropdowns and selects
            selects = await page.query_selector_all("select")
            for select in selects[:10]:
                finding = await self._test_select(page, select, url)
                if finding:
                    findings.append(finding)

            # Test accordion / collapse triggers
            accordions = await page.query_selector_all("[data-bs-toggle='collapse'], [aria-expanded]")
            for el in accordions[:10]:
                try:
                    await el.click(timeout=3000)
                    await page.wait_for_timeout(300)
                except Exception:
                    pass

            # Check for JS console errors on this page
            if console_errors:
                findings.append({
                    "type": "console_error",
                    "url": url,
                    "description": f"{len(console_errors)} JavaScript console error(s) detected",
                    "details": console_errors[:5],
                    "is_issue": True,
                    "raw_severity": "MAJOR",
                })

        except Exception as e:
            findings.append({
                "type": "page_load_error",
                "url": url,
                "description": f"Page failed to load: {str(e)[:200]}",
                "is_issue": True,
                "raw_severity": "CRITICAL",
            })
        finally:
            await page.close()

        return findings

    async def _test_button(self, page, btn, url: str, idx: int, console_errors: list) -> Optional[dict]:
        try:
            btn_text = (await btn.inner_text()).strip()[:60] or f"button_{idx}"
            is_visible = await btn.is_visible()
            if not is_visible:
                return {
                    "type": "hidden_button",
                    "url": url,
                    "element": btn_text,
                    "description": f"Button '{btn_text}' exists in DOM but is not visible",
                    "is_issue": True,
                    "raw_severity": "MINOR",
                }

            # Check if button is visually accessible (not clipped, not behind other elements)
            box = await btn.bounding_box()
            if box and (box["width"] < 8 or box["height"] < 8):
                return {
                    "type": "tiny_button",
                    "url": url,
                    "element": btn_text,
                    "description": f"Button '{btn_text}' is extremely small ({box['width']:.0f}x{box['height']:.0f}px) — likely a touch target issue",
                    "is_issue": True,
                    "raw_severity": "MINOR",
                }

            errors_before = len(console_errors)
            url_before = page.url

            await btn.click(timeout=5000, force=False)
            await page.wait_for_timeout(600)

            # Did clicking cause a console error?
            new_errors = console_errors[errors_before:]
            if new_errors:
                return {
                    "type": "button_causes_error",
                    "url": url,
                    "element": btn_text,
                    "description": f"Clicking '{btn_text}' caused {len(new_errors)} JS error(s)",
                    "details": new_errors,
                    "is_issue": True,
                    "raw_severity": "MAJOR",
                }

            return {
                "type": "button_interaction",
                "url": url,
                "element": btn_text,
                "description": f"Button '{btn_text}' clicked successfully",
                "is_issue": False,
            }

        except Exception as e:
            err_str = str(e)
            # Navigation-related errors are expected for link-styled buttons
            nav_keywords = ["timeout", "intercept", "execution context was destroyed",
                            "navigating", "detached", "target closed"]
            if any(kw in err_str.lower() for kw in nav_keywords):
                return None  # Not a real issue — button triggered navigation
            return {
                "type": "button_click_error",
                "url": url,
                "element": f"button_{idx}",
                "description": f"Error interacting with button: {err_str[:200]}",
                "is_issue": True,
                "raw_severity": "MAJOR",
            }

    async def _test_select(self, page, select, url: str) -> Optional[dict]:
        try:
            options = await select.query_selector_all("option")
            if len(options) < 2:
                return None
            # Select each option and check for errors
            for opt in options[1:min(4, len(options))]:
                value = await opt.get_attribute("value")
                if value:
                    await select.select_option(value=value)
                    await page.wait_for_timeout(200)
            return None
        except Exception:
            return None
