"""CitizenRIMS generic adapter for jail rosters.

URL: https://<agency>.citizenrims.com/incarcerated-people
Table: Booking # | Name | Booking Date | Arresting Agency | Arrest Location | Bail | Status

One adapter covers all CitizenRIMS tenants — the roster page is a plain HTML
table with consistent column order. Records land in staging only; a human
promotes to public after verifying the first snapshot.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Dict, List

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized


class _TableExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: List[List[List[str]]] = []
        self._rows: List[List[str]] = []
        self._row: List[str] = []
        self._cell_parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self._row = []
        elif tag in ('td', 'th'):
            self._cell_parts = []
        elif tag == 'br':
            self._cell_parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self._row.append(re.sub(r'\s+', ' ', ''.join(self._cell_parts)).strip())
        elif tag == 'tr':
            if self._row:
                self._rows.append(self._row)
        elif tag == 'table':
            if self._rows:
                self.tables.append(self._rows)
                self._rows = []

    def handle_data(self, data):
        self._cell_parts.append(data)


def _parse_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw or raw in ("—", "-"):
        return None
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %I:%M%p", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def _parse_bail(raw: str) -> float | None:
    raw = (raw or "").strip().replace(",", "")
    if not raw or raw in ("—", "-", "$0"):
        return None
    m = re.search(r"(\d+(?:\.\d{2})?)", raw)
    return float(m.group(1)) if m else None


def _parse_name(raw: str) -> tuple:
    name = (raw or "").strip()
    if not name:
        return "", ""
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        return first.title(), last.title()
    parts = name.split()
    if len(parts) == 1:
        return "", parts[0].title()
    return parts[0].title(), " ".join(parts[1:]).title()


def fetch(source) -> AdapterResult:
    url = source.get("source_url") or ""
    _assert_authorized(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    response = httpx.get(url, timeout=45, follow_redirects=True, headers=headers)
    response.raise_for_status()
    parser = _TableExtractor()
    parser.feed(response.text)

    if not parser.tables:
        return AdapterResult(source, [])

    table = parser.tables[0]
    records = []

    for row in table:
        if not row or not row[0].strip():
            continue
        first, last = _parse_name(row[1] if len(row) > 1 else "")
        bail = _parse_bail(row[5] if len(row) > 5 else "")
        booking_date = _parse_date(row[2] if len(row) > 2 else "")
        records.append({
            "state": source.get("state", ""),
            "county": source.get("county", ""),
            "facility": source.get("facility_name", ""),
            "source_url": url,
            "source_type": "citizenrims",
            "pulled_at": datetime.now(timezone.utc).isoformat(),
            "source_id": row[0],
            "booking_number": row[0],
            "source_updated_at": booking_date or datetime.now(timezone.utc).isoformat(),
            "visibility": "public",
            "full_name": f"{first} {last}".strip(),
            "first_name": first,
            "last_name": last,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "release_date": None,
            "charges": [],
            "bond_amount": bail,
            "bonds": [],
            "status": row[6].lower() if len(row) > 6 and row[6] else "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
