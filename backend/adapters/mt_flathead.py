"""Flathead County MT jail roster adapter.

Port of /root/montanablotter/services/ingestion/fetchers/flathead_inmate.py
(page structure proven in production since 2024). Roster is a plain HTML
page: https://apps.flathead.mt.gov/jailroster/?report=inmates&sort=lastname
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List

from backend.adapters.idaho import AdapterResult, _assert_authorized

_BASE = "https://apps.flathead.mt.gov/jailroster/"
_FALLBACK_CHARGES = "Charge details available on the official Flathead County inmate page."


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "hr"}:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "div", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._parts.append("\n")

    def handle_data(self, data):
        if data:
            self._parts.append(data)

    def text(self) -> str:
        text = unescape("".join(self._parts)).replace("\xa0", " ")
        return re.sub(r"\s+", " ", text).strip()


def _text(fragment: str) -> str:
    parser = _TextExtractor()
    parser.feed(fragment or "")
    return parser.text()


def _fetch(url: str) -> str:
    import httpx
    _assert_authorized(url)
    response = httpx.get(url, timeout=45, follow_redirects=True, verify=False, headers={
        "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
        "Accept": "text/html,application/xhtml+xml",
    })
    response.raise_for_status()
    return response.text


def fetch(source) -> AdapterResult:
    url = (source["source_url"] or _BASE).rstrip("/") + "/?report=inmates&sort=lastname"
    page_html = _fetch(url)
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    entries = re.findall(
        r'(?:<article\s+class="inmate-entry"\s*>(.*?)</article>'
        r'|<div class="inmate-entry">\s*(.*?)<div class="inmate-entry-footer"></div>\s*</div>)',
        page_html, re.IGNORECASE | re.DOTALL)
    entries = [next((part for part in match if part), "") for match in entries]

    for entry in entries:
        name_match = re.search(r'<div class="inmate-name">\s*<h2[^>]*>(.*?)</h2>', entry,
                               re.IGNORECASE | re.DOTALL)
        if not name_match:
            continue
        raw_name = _text(name_match.group(1))
        if "," in raw_name:
            last_name, first_name = [p.strip() for p in raw_name.split(",", 1)]
        else:
            parts = raw_name.split()
            first_name, last_name = (parts[0], " ".join(parts[1:])) if parts else ("", "")

        def stat(label: str) -> str:
            m = re.search(
                rf'<div class="inmate-stat">\s*(?:<h6>\s*{label}:\s*</h6>'
                rf'|<span class="stat-label">\s*{label}:\s*</span>)\s*<p>(.*?)</p>\s*</div>',
                entry, re.IGNORECASE | re.DOTALL)
            return _text(m.group(1)) if m else ""

        age_value = stat("Age")
        pin_value = stat("PIN")
        mug_match = re.search(r"url\('images/inmates/([^']+)'\)", entry, re.IGNORECASE)
        booking_number = re.sub(r"\.[A-Za-z0-9]+$", "", mug_match.group(1)).strip() if mug_match else ""
        if not booking_number:
            booking_number = pin_value
        charge_matches = re.findall(
            r'<p[^>]*class="disposition-description[^"]*"[^>]*>(.*?)</p>',
            entry, re.IGNORECASE | re.DOTALL)
        charges = [_text(m) for m in charge_matches if _text(m)]
        if not charges:
            charges = [_FALLBACK_CHARGES]
        mugshot_url = (f"https://apps.flathead.mt.gov/jailroster/images/inmates/{mug_match.group(1)}"
                       if mug_match else None)

        records.append({
            "state": "MT",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "id": booking_number or pin_value or raw_name.lower().replace(" ", "-"),
            "booking_number": booking_number or pin_value or f"FH-{booking_number or pin_value or raw_name.lower().replace(' ', '-')}",
            "source_updated_at": pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at,
            "visibility": "public",
            "full_name": f"{last_name.title()}, {first_name.title()}".strip(", "),
            "first_name": first_name.title(),
            "last_name": last_name.title(),
            "dob": None,
            "age": int(age_value) if age_value.isdigit() else None,
            "sex": None,
            "race": None,
            "booking_date": pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at,
            "release_date": None,
            "charges": [{"source_id": f"chg-{i}", "description": c[:2000], "statute": None, "severity": None}
                        for i, c in enumerate(charges[:5])],
            "bonds": [],
            "bond_amount": None,
            "status": "in_custody",
            "mugshot_url": mugshot_url,
            "notes": None,
        })
    return AdapterResult(source, records)
