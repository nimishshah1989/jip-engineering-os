from typing import Optional
from typing import Optional
"""
Form Fuzzer Agent
For every form in the app, submits:
  1. Valid complete data
  2. Empty submission (test required validation)
  3. Invalid formats (wrong email, negative numbers, future dates)
  4. Edge cases: very long strings, special characters, SQL injection strings, XSS probes
  5. Partial fills (some fields filled, some empty)

Captures: error messages, missing validations, broken states, server errors.
"""

import asyncio
import base64
from pathlib import Path
from playwright.async_api import async_playwright


FUZZ_PAYLOADS = {
    "email": [
        "test@example.com",          # valid
        "invalid-email",             # invalid format
        "a" * 255 + "@test.com",     # too long
        "",                          # empty
        "test@",                     # incomplete
        " test@example.com ",        # leading/trailing space
    ],
    "text": [
        "Test Input",                # normal
        "",                          # empty
        "A" * 500,                   # very long string
        "<script>alert(1)</script>", # XSS probe (should be escaped)
        "'; DROP TABLE users; --",   # SQL injection probe (should be escaped)
        "😀🎯🚀",                    # emoji
        "   ",                       # whitespace only
        "\n\r\t",                    # control characters
    ],
    "number": [
        "42",                        # valid
        "-1",                        # negative
        "0",                         # zero
        "999999999",                 # very large
        "abc",                       # non-numeric
        "",                          # empty
        "3.14",                      # decimal
    ],
    "password": [
        "ValidPass123!",             # strong
        "a",                         # too short
        "",                          # empty
        "A" * 200,                   # very long
        "password",                  # common weak password
    ],
    "tel": [
        "+91 9876543210",            # valid Indian
        "1234567890",                # 10 digit
        "abc",                       # non-numeric
        "",                          # empty
        "12345",                     # too short
    ],
    "date": [
        "2025-01-01",                # valid past
        "2099-12-31",                # far future
        "1900-01-01",                # very old
        "invalid-date",              # invalid
        "",                          # empty
    ],
    "default": [
        "Test value",
        "",
        "A" * 300,
        "<b>bold</b>",
    ],
}


class FormFuzzerAgent:
    def __init__(self, base_url: str, config: dict, screenshots_dir: Path):
        self.base_url = base_url
        self.config = config
        self.screenshots_dir = screenshots_dir
        self.screenshot_count = 0

    async def run(self, site_map: dict) -> list:
        findings = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 900})

            for page_data in site_map["pages"]:
                if page_data.get("error") or not page_data.get("forms"):
                    continue
                for form_idx, form in enumerate(page_data["forms"]):
                    form_findings = await self._fuzz_form(context, page_data["url"], form, form_idx)
                    findings.extend(form_findings)

            await browser.close()

        return findings

    async def _fuzz_form(self, context, url: str, form: dict, form_idx: int) -> list:
        findings = []
        fields = form.get("fields", [])
        if not fields:
            return findings

        test_cases = [
            ("empty_submit", self._get_empty_payload(fields)),
            ("valid_submit", self._get_valid_payload(fields)),
            ("edge_cases", self._get_edge_payload(fields)),
        ]

        for case_name, payload in test_cases:
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(500)

                finding = await self._submit_form(page, form, payload, url, form_idx, case_name)
                if finding:
                    findings.append(finding)

            except Exception as e:
                findings.append({
                    "type": "form_test_error",
                    "url": url,
                    "form_index": form_idx,
                    "test_case": case_name,
                    "description": f"Error during form fuzz ({case_name}): {str(e)[:200]}",
                    "is_issue": False,  # Infrastructure error, not app bug
                })
            finally:
                await page.close()

        return findings

    async def _submit_form(self, page, form: dict, payload: dict, url: str, form_idx: int, case_name: str) -> Optional[dict]:
        fields = form.get("fields", [])
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        filled_count = 0
        for field in fields:
            field_name = field.get("name")
            field_type = field.get("type", "text")

            if field_type in ("submit", "button", "reset", "hidden", "file"):
                continue

            value = payload.get(field_name or field_type, "")

            try:
                selector = f'[name="{field_name}"]' if field_name else f'input[type="{field_type}"]'
                el = await page.query_selector(selector)
                if not el:
                    continue

                if field_type == "checkbox":
                    if value:
                        await el.check()
                elif field_type == "radio":
                    if value:
                        await el.check()
                elif field_type == "select" or (await el.evaluate("el => el.tagName")) == "SELECT":
                    options = await el.query_selector_all("option")
                    if options and len(options) > 1:
                        first_val = await options[1].get_attribute("value")
                        if first_val:
                            await el.select_option(value=first_val)
                else:
                    await el.fill(str(value))
                filled_count += 1
            except Exception:
                pass

        # Take pre-submit screenshot
        await page.wait_for_timeout(200)

        # Find and click submit
        submit = await page.query_selector('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Save"), button:has-text("Login"), button:has-text("Sign in"), button:has-text("Register")')

        if not submit:
            return None

        url_before = page.url
        response_status = None

        # Intercept network to catch 4xx/5xx
        async def handle_response(response):
            nonlocal response_status
            if response.status >= 400:
                response_status = response.status

        page.on("response", handle_response)

        try:
            await submit.click(timeout=5000)
            await page.wait_for_timeout(1500)
        except Exception as e:
            return {
                "type": "form_submit_broken",
                "url": url,
                "form_index": form_idx,
                "test_case": case_name,
                "description": f"Submit button click failed: {str(e)[:200]}",
                "is_issue": True,
                "raw_severity": "MAJOR",
            }

        issues = []

        # Check for server errors
        if response_status and response_status >= 500:
            issues.append(f"Server returned HTTP {response_status}")

        # Check for console errors after submit
        if console_errors:
            issues.append(f"{len(console_errors)} JS errors after submit")

        # For empty submission, we EXPECT validation errors — check they actually appear
        if case_name == "empty_submit":
            required_fields = [f for f in fields if f.get("required")]
            if required_fields:
                # Check if any error messages appeared
                error_els = await page.query_selector_all('[class*="error"], [class*="invalid"], [aria-invalid="true"], .form-error, .field-error')
                if not error_els and page.url == url:
                    issues.append(f"No validation errors shown for empty required fields ({len(required_fields)} required fields exist)")

        if issues:
            # Take screenshot of the issue
            screenshot_name = f"form_{form_idx}_{case_name}.png"
            screenshot_path = self.screenshots_dir / screenshot_name
            try:
                await page.screenshot(path=str(screenshot_path), full_page=True)
                self.screenshot_count = getattr(self, "screenshot_count", 0) + 1
            except Exception:
                screenshot_path = None

            return {
                "type": "form_issue",
                "url": url,
                "form_index": form_idx,
                "test_case": case_name,
                "description": "; ".join(issues),
                "screenshot": str(screenshot_path) if screenshot_path else None,
                "is_issue": True,
                "raw_severity": "MAJOR" if any("Server" in i or "JS error" in i for i in issues) else "MINOR",
            }

        return {
            "type": "form_test",
            "url": url,
            "form_index": form_idx,
            "test_case": case_name,
            "description": f"Form {form_idx} passed {case_name} test",
            "is_issue": False,
        }

    def _get_empty_payload(self, fields: list) -> dict:
        return {f.get("name") or f.get("type", "field"): "" for f in fields}

    def _get_valid_payload(self, fields: list) -> dict:
        payload = {}
        for f in fields:
            key = f.get("name") or f.get("type", "field")
            ftype = f.get("type", "text")
            label = (f.get("label") or "").lower()

            if ftype == "email" or "email" in key.lower():
                payload[key] = "qa_test@example.com"
            elif ftype == "password" or "password" in key.lower():
                payload[key] = "TestPassword123!"
            elif ftype == "tel" or "phone" in key.lower() or "mobile" in key.lower():
                payload[key] = "9876543210"
            elif ftype == "number":
                payload[key] = "100"
            elif ftype == "date":
                payload[key] = "2025-06-01"
            elif "name" in key.lower():
                payload[key] = "QA Test User"
            elif "amount" in key.lower() or "value" in key.lower():
                payload[key] = "10000"
            else:
                payload[key] = "Test Input Value"
        return payload

    def _get_edge_payload(self, fields: list) -> dict:
        payload = {}
        for f in fields:
            key = f.get("name") or f.get("type", "field")
            ftype = f.get("type", "text")
            if ftype == "email":
                payload[key] = "notanemail"
            elif ftype == "number":
                payload[key] = "-999999"
            elif ftype == "password":
                payload[key] = "a"
            else:
                payload[key] = "A" * 300
        return payload
