from __future__ import annotations

from typing import Any, Iterable

from ..base import BaseAdapter
from ..models import BookingRecord
from .html_table import HtmlTableAdapter


class PlaywrightFormAdapter(HtmlTableAdapter):
    """Renders a roster, optionally submits a public search form, then parses its table."""

    def fetch(self) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright adapter requires the optional playwright package and Chromium") from exc

        options = self.config.options
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(user_agent="JailMapRosterIndexer/1.0 (+https://jailmap.com/contact)")
            page.goto(self.config.source_url, wait_until="domcontentloaded", timeout=int(options.get("timeout_ms", 30_000)))
            for selector, value in options.get("form_fields", {}).items():
                page.locator(selector).fill(str(value))
            if options.get("submit_selector"):
                page.locator(options["submit_selector"]).click()
            page.wait_for_selector(options.get("table_selector", "table"), timeout=int(options.get("timeout_ms", 30_000)))
            html = page.content()
            browser.close()
            return html

    def parse(self, artifact: str) -> Iterable[dict[str, Any]]:
        return super().parse(artifact)

    def normalize(self, item: dict[str, Any]) -> BookingRecord:
        return super().normalize(item)
