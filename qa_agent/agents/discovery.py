"""
Discovery Agent
Crawls the target app and builds a complete map of:
  - All pages / routes
  - All forms and their fields
  - All buttons and interactive elements
  - All links (internal)
  - Inferred user flows
"""

import asyncio
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright


class DiscoveryAgent:
    def __init__(self, base_url: str, config: dict):
        self.base_url = base_url.rstrip("/")
        self.config = config
        self.visited = set()
        self.pages_data = []

    async def run(self) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="JIP-QA-Agent/1.0 (automated testing)",
            )

            # Intercept and log console errors
            page = await context.new_page()
            page.on("console", lambda msg: None)  # captured per-page in sub-agents

            await self._crawl(page, self.base_url)

            await browser.close()

        return self._build_site_map()

    async def _crawl(self, page, url: str, depth: int = 0):
        max_depth = self.config.get("crawl", {}).get("max_depth", 3)
        max_pages = self.config.get("crawl", {}).get("max_pages", 50)

        if depth > max_depth or len(self.visited) >= max_pages:
            return
        if url in self.visited:
            return
        if not url.startswith(self.base_url):
            return

        self.visited.add(url)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # networkidle timeout is fine, page is already loaded
            await page.wait_for_timeout(500)

            page_data = await self._extract_page_data(page, url)
            self.pages_data.append(page_data)

            # Recurse into internal links
            for link in page_data.get("internal_links", []):
                await self._crawl(page, link, depth + 1)

        except Exception as e:
            self.pages_data.append({
                "url": url,
                "error": str(e),
                "forms": [],
                "buttons": [],
                "inputs": [],
                "internal_links": [],
            })

    async def _extract_page_data(self, page, url: str) -> dict:
        title = await page.title()

        # Extract all forms
        forms = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('form')).map((form, i) => ({
                index: i,
                id: form.id || null,
                action: form.action || null,
                method: form.method || 'get',
                fields: Array.from(form.querySelectorAll('input, select, textarea')).map(el => ({
                    type: el.type || el.tagName.toLowerCase(),
                    name: el.name || el.id || null,
                    placeholder: el.placeholder || null,
                    required: el.required,
                    label: (() => {
                        const lbl = document.querySelector(`label[for="${el.id}"]`);
                        return lbl ? lbl.textContent.trim() : null;
                    })(),
                }))
            }));
        }""")

        # Extract all buttons
        buttons = await page.evaluate("""() => {
            const els = document.querySelectorAll('button, [role="button"], input[type="submit"], a.btn, a[class*="button"]');
            return Array.from(els).slice(0, 100).map(el => ({
                text: el.textContent.trim().substring(0, 80),
                type: el.getAttribute('type') || 'button',
                disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
                selector: el.id ? `#${el.id}` : (el.className ? `.${el.className.trim().split(' ')[0]}` : el.tagName.toLowerCase()),
            }));
        }""")

        # Extract all inputs (outside forms too)
        inputs = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input, select, textarea')).slice(0, 100).map(el => ({
                type: el.type || el.tagName.toLowerCase(),
                name: el.name || el.id || null,
                placeholder: el.placeholder || null,
                required: el.required,
            }));
        }""")

        # Extract internal links
        links = await page.evaluate(f"""() => {{
            const base = '{self.base_url}';
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href)
                .filter(href => href.startsWith(base) && !href.includes('#') && !href.includes('mailto:'))
                .slice(0, 30);
        }}""")

        # Extract nav items (to infer flows)
        nav_items = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('nav a, [role="navigation"] a')).map(a => ({
                text: a.textContent.trim(),
                href: a.href,
            })).slice(0, 20);
        }""")

        # Detect modals / dialogs
        modal_triggers = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('[data-toggle="modal"], [data-bs-toggle="modal"], [aria-haspopup="dialog"]'))
                .map(el => ({ text: el.textContent.trim(), target: el.dataset.bsTarget || el.dataset.target }))
                .slice(0, 10);
        }""")

        return {
            "url": url,
            "title": title,
            "forms": forms,
            "buttons": buttons,
            "inputs": inputs,
            "internal_links": list(set(links)),
            "nav_items": nav_items,
            "modal_triggers": modal_triggers,
        }

    def _build_site_map(self) -> dict:
        total_forms = sum(len(p.get("forms", [])) for p in self.pages_data)
        total_buttons = sum(len(p.get("buttons", [])) for p in self.pages_data)
        total_inputs = sum(len(p.get("inputs", [])) for p in self.pages_data)

        # Infer user flows from nav structure
        flows = self._infer_flows()

        return {
            "pages": self.pages_data,
            "total_forms": total_forms,
            "total_buttons": total_buttons,
            "total_inputs": total_inputs,
            "flows": flows,
            "all_urls": list(self.visited),
        }

    def _infer_flows(self) -> list:
        flows = []
        # Detect login flow
        for page in self.pages_data:
            url = page.get("url", "")
            if any(kw in url for kw in ["login", "signin", "auth"]):
                flows.append({"name": "Authentication", "start_url": url, "type": "auth"})
            if any(kw in url for kw in ["register", "signup", "onboard"]):
                flows.append({"name": "Registration/Onboarding", "start_url": url, "type": "onboarding"})
            if any(kw in url for kw in ["dashboard", "home", "overview"]):
                flows.append({"name": "Main Dashboard", "start_url": url, "type": "dashboard"})
            for form in page.get("forms", []):
                if any(f.get("type") == "password" for f in form.get("fields", [])):
                    if {"name": "Authentication", "start_url": url, "type": "auth"} not in flows:
                        flows.append({"name": "Authentication", "start_url": url, "type": "auth"})

        if not flows:
            flows.append({"name": "Main Page", "start_url": self.base_url, "type": "general"})

        return flows
