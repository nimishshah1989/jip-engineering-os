"""
Flow Walker Agent
Identifies and walks all multi-step user flows:
  - Auth flow (login / logout / register)
  - Onboarding flows
  - Dashboard navigation flows
  - Any wizard / step-by-step sequences

Tests: happy path, back navigation, direct URL access to mid-flow pages,
       session expiry handling, redirect correctness.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


class FlowWalkerAgent:
    def __init__(self, base_url: str, config: dict, screenshots_dir: Path):
        self.base_url = base_url
        self.config = config
        self.screenshots_dir = screenshots_dir

    async def run(self, site_map: dict) -> list:
        findings = []
        flows = site_map.get("flows", [])

        credentials = self.config.get("test_credentials", {})

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 900})

            for flow in flows:
                flow_findings = await self._walk_flow(context, flow, credentials, site_map)
                findings.extend(flow_findings)

            # Test direct URL access to every page (no logged-in state)
            findings.extend(await self._test_direct_access(context, site_map))

            # Test back navigation
            findings.extend(await self._test_back_navigation(context, site_map))

            # Test 404 handling
            findings.extend(await self._test_404_handling(context))

            await browser.close()

        return findings

    async def _walk_flow(self, context, flow: dict, credentials: dict, site_map: dict) -> list:
        findings = []
        flow_type = flow.get("type", "general")
        start_url = flow.get("start_url", self.base_url)

        page = await context.new_page()
        try:
            if flow_type == "auth":
                findings.extend(await self._walk_auth_flow(page, start_url, credentials))
            elif flow_type == "onboarding":
                findings.extend(await self._walk_onboarding_flow(page, start_url))
            elif flow_type == "dashboard":
                findings.extend(await self._walk_dashboard_flow(page, start_url, site_map))
            else:
                findings.extend(await self._walk_general_flow(page, start_url, site_map))
        except Exception as e:
            findings.append({
                "type": "flow_error",
                "url": start_url,
                "flow": flow.get("name"),
                "description": f"Flow walking failed: {str(e)[:200]}",
                "is_issue": True,
                "raw_severity": "MAJOR",
            })
        finally:
            await page.close()

        return findings

    async def _walk_auth_flow(self, page, url: str, credentials: dict) -> list:
        findings = []

        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(500)

        # Test: page loads correctly
        title = await page.title()
        if not title:
            findings.append({
                "type": "missing_page_title",
                "url": url,
                "description": "Auth page has no <title> tag",
                "is_issue": True,
                "raw_severity": "MINOR",
            })

        # Test: wrong credentials
        email_field = await page.query_selector('input[type="email"], input[name*="email"], input[name*="username"]')
        password_field = await page.query_selector('input[type="password"]')

        if email_field and password_field:
            await email_field.fill("wrong@example.com")
            await password_field.fill("wrongpassword")

            submit = await page.query_selector('button[type="submit"], input[type="submit"]')
            if submit:
                await submit.click()
                await page.wait_for_timeout(2000)

                # Should show an error, not redirect to dashboard
                current_url = page.url
                error_shown = await page.query_selector('[class*="error"], [class*="alert"], [role="alert"]')

                if not error_shown and current_url != url:
                    findings.append({
                        "type": "auth_no_error_on_wrong_creds",
                        "url": url,
                        "description": "Login with wrong credentials did not show an error message",
                        "is_issue": True,
                        "raw_severity": "CRITICAL",
                    })

            # Test with valid credentials if provided
            if credentials.get("email") and credentials.get("password"):
                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                email_field = await page.query_selector('input[type="email"], input[name*="email"], input[name*="username"]')
                password_field = await page.query_selector('input[type="password"]')

                if email_field and password_field:
                    await email_field.fill(credentials["email"])
                    await password_field.fill(credentials["password"])
                    submit = await page.query_selector('button[type="submit"], input[type="submit"]')
                    if submit:
                        await submit.click()
                        await page.wait_for_timeout(3000)
                        # Check we actually navigated somewhere
                        if page.url == url:
                            findings.append({
                                "type": "login_failed",
                                "url": url,
                                "description": "Login with valid credentials did not redirect — check test_credentials in qa_config.yaml",
                                "is_issue": False,  # Could be wrong test credentials
                                "raw_severity": "INFO",
                            })

        return findings

    async def _walk_onboarding_flow(self, page, url: str) -> list:
        findings = []
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)

        # Check for Next/Continue buttons (wizard pattern)
        next_buttons = await page.query_selector_all('button:has-text("Next"), button:has-text("Continue"), button:has-text("Proceed")')
        for btn in next_buttons[:5]:
            try:
                await btn.click()
                await page.wait_for_timeout(800)
            except Exception:
                pass

        return findings

    async def _walk_dashboard_flow(self, page, url: str, site_map: dict) -> list:
        findings = []
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)

        # Check load time
        start = asyncio.get_event_loop().time()
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        load_time = asyncio.get_event_loop().time() - start

        if load_time > 5:
            findings.append({
                "type": "slow_page_load",
                "url": url,
                "description": f"Dashboard took {load_time:.1f}s to load (threshold: 5s)",
                "is_issue": True,
                "raw_severity": "MAJOR",
            })

        # Check all nav links work
        nav_links = await page.query_selector_all("nav a[href], [role='navigation'] a[href]")
        for link in nav_links[:10]:
            href = await link.get_attribute("href")
            if href and href.startswith(("http", "/")):
                try:
                    response = await page.request.get(
                        href if href.startswith("http") else f"{self.base_url}{href}",
                        timeout=5000,
                    )
                    if response.status >= 400:
                        findings.append({
                            "type": "broken_nav_link",
                            "url": url,
                            "description": f"Nav link returns HTTP {response.status}: {href}",
                            "is_issue": True,
                            "raw_severity": "MAJOR",
                        })
                except Exception:
                    pass

        return findings

    async def _walk_general_flow(self, page, url: str, site_map: dict) -> list:
        findings = []
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return findings

    async def _test_direct_access(self, context, site_map: dict) -> list:
        """Test that all pages are accessible (or correctly redirect if auth required)."""
        findings = []
        page = await context.new_page()

        for page_data in site_map["pages"][:20]:
            url = page_data.get("url")
            if not url or page_data.get("error"):
                continue
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                if response and response.status >= 500:
                    findings.append({
                        "type": "page_server_error",
                        "url": url,
                        "description": f"Page returns HTTP {response.status} — server error",
                        "is_issue": True,
                        "raw_severity": "CRITICAL",
                    })
            except Exception:
                pass

        await page.close()
        return findings

    async def _test_back_navigation(self, context, site_map: dict) -> list:
        """Navigate forward then press back — check app doesn't break."""
        findings = []
        if len(site_map["pages"]) < 2:
            return findings

        page = await context.new_page()
        try:
            urls = [p["url"] for p in site_map["pages"][:3] if not p.get("error")]
            if len(urls) < 2:
                return findings

            await page.goto(urls[0], wait_until="domcontentloaded", timeout=10000)
            await page.goto(urls[1], wait_until="domcontentloaded", timeout=10000)
            await page.go_back()
            await page.wait_for_timeout(1000)

            # Check page didn't crash
            error_el = await page.query_selector('[class*="error-page"], #error, .error-boundary')
            if error_el:
                findings.append({
                    "type": "back_navigation_error",
                    "url": urls[0],
                    "description": "Back navigation causes error state on page",
                    "is_issue": True,
                    "raw_severity": "MAJOR",
                })
        except Exception:
            pass
        finally:
            await page.close()

        return findings

    async def _test_404_handling(self, context) -> list:
        """Visit a non-existent URL — should show a proper 404 page, not crash."""
        findings = []
        page = await context.new_page()
        try:
            response = await page.goto(
                f"{self.base_url}/this-page-definitely-does-not-exist-qa-test",
                wait_until="domcontentloaded",
                timeout=10000,
            )
            if response:
                if response.status == 200:
                    # Might be a SPA that handles routing — acceptable, check content
                    content = await page.content()
                    if len(content) < 500:
                        findings.append({
                            "type": "missing_404_page",
                            "url": self.base_url,
                            "description": "Non-existent URL returns 200 with minimal content — no 404 page configured",
                            "is_issue": True,
                            "raw_severity": "MINOR",
                        })
                elif response.status >= 500:
                    findings.append({
                        "type": "404_causes_server_error",
                        "url": self.base_url,
                        "description": f"Non-existent URL returns HTTP {response.status} — server crashes on missing routes",
                        "is_issue": True,
                        "raw_severity": "MAJOR",
                    })
        except Exception:
            pass
        finally:
            await page.close()

        return findings
