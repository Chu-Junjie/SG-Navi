"""Optional browser smoke tests using controlled local fixtures (no real network).

Install Playwright and Chromium; run from repository root:
  python frontend/tests/browser_task4.py

This is intentionally not discovered by unittest in CI.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

FRONTEND = Path(__file__).resolve().parents[1]


def run_checks():
    files = [
        "schemas/rental_deposit_input.schema.json",
        "schemas/consumer_complaint_input.schema.json",
        "schemas/action_card.schema.json",
        "mappings/task3_display_map.json",
        "mocks/need_clarification_response.json",
        "mocks/supported_path_response.json",
        "mocks/refer_to_official_response.json",
        "mocks/error_response.json",
    ]
    fixture_data = {"./" + item: json.loads((FRONTEND / item).read_text(encoding="utf-8")) for item in files}
    html = (FRONTEND / "forms.html").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="./css/task4-forms.css">', "")
    html = html.replace('<script src="./js/task4-forms.js" defer></script>', "")
    css = (FRONTEND / "css/task4-forms.css").read_text(encoding="utf-8")
    script = (FRONTEND / "js/task4-forms.js").read_text(encoding="utf-8")
    checks = 0
    with sync_playwright() as p:
        options = {"executable_path": os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]} if os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE") else {}
        browser = p.chromium.launch(headless=True, **options)
        try:
            for width in (1440, 390, 320):
                page = browser.new_page(viewport={"width": width, "height": 850})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.set_content(html)
                page.add_style_tag(content=css)
                page.evaluate("""fixtures => {
                    window.__liveApiCalls = 0;
                    window.fetch = async (path, options) => {
                        if (String(path).includes('/api/')) {
                            window.__liveApiCalls++;
                            throw new Error('Live API must not be used in mock preview');
                        }
                        if (!Object.prototype.hasOwnProperty.call(fixtures, path))
                            return new Response('Not found', {status:404});
                        return new Response(JSON.stringify(fixtures[path]), {
                            status:200, headers:{'Content-Type':'application/json'}
                        });
                    };
                }""", fixture_data)
                page.add_script_tag(content=script)
                page.locator(".field").first.wait_for()
                for case_type in ("rental_deposit", "consumer_complaint"):
                    page.select_option("#case-type", case_type)
                    assert page.locator(".field").count() == 9, case_type
                    for status in ("NEED_CLARIFICATION", "SUPPORTED_PATH", "REFER_TO_OFFICIAL", "ERROR"):
                        page.select_option("#mock-status", status)
                        page.click("#submit-form")
                        page.wait_for_function("expected => document.getElementById('result-status').textContent === expected", arg=status)
                        assert page.locator(".result-section").count() == 7
                        assert "Needs verification" in page.locator("#evidence-alert").inner_text()
                        checks += 1
                page.select_option("#case-type", "rental_deposit")
                row = page.locator('[data-field="claim_amount_sgd"]')
                row.locator(".field-state select").select_option("value")
                value = row.locator(".field-value input")
                value.fill("-5")
                page.click("#submit-form")
                assert value.get_attribute("aria-invalid") == "true"
                value.fill("100")
                page.click("#submit-form")
                page.wait_for_function("document.getElementById('result-status').textContent === 'ERROR'")
                row.locator(".field-state select").select_option("unknown")
                page.select_option("#case-type", "consumer_complaint")
                page.select_option("#case-type", "rental_deposit")
                assert row.locator(".field-state select").input_value() == "unknown"
                assert not errors, errors
                assert page.evaluate("window.__liveApiCalls === 0")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
                page.close()
        finally:
            browser.close()
    print(f"PASS {checks} combinations; validation, edits, unknown, mobile overflow, JS errors, no live API calls")


if __name__ == "__main__":
    run_checks()
