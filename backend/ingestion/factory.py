from __future__ import annotations

from typing import Type

from .adapters import HtmlTableAdapter, JsonApiAdapter, MinnehahaRosterAdapter, PdfRosterAdapter, PlaywrightFormAdapter
from .base import AdapterConfig, BaseAdapter


DRIVERS: dict[str, Type[BaseAdapter]] = {
    "html_table": HtmlTableAdapter,
    "static_html": HtmlTableAdapter,
    "php_table": HtmlTableAdapter,
    "synergistic": HtmlTableAdapter,
    "pdf_roster": PdfRosterAdapter,
    "static_pdf": PdfRosterAdapter,
    "json_api": JsonApiAdapter,
    "rest_api": JsonApiAdapter,
    "playwright_form": PlaywrightFormAdapter,
    "aspnet_form": PlaywrightFormAdapter,
    "jms_portal": PlaywrightFormAdapter,
    "minnehaha_html": MinnehahaRosterAdapter,
    "smartcop": PlaywrightFormAdapter,
    "tyler_json": JsonApiAdapter,
}


def build_adapter(config: AdapterConfig, client=None) -> BaseAdapter:
    driver = (config.vendor or "").lower()
    if driver in {"appriss", "vine"}:
        raise ValueError("VINE/Appriss requires an authorized API agreement; no public scraping driver is provided")
    try:
        adapter_class = DRIVERS[driver]
    except KeyError as exc:
        raise ValueError(f"unknown adapter driver: {driver!r}; choose one of {', '.join(sorted(DRIVERS))}") from exc
    return adapter_class(config, client=client)
