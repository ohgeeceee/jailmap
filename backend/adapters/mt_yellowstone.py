"""Yellowstone County MT jail roster adapter.

Port of /root/montanablotter/services/ingestion/fetchers/yellowstone_inmate.py.
The dcsearch.asp page gates the roster behind a simple arithmetic prompt
(solve and POST back). Table has 8 columns: last, first, middle, jacket
number, housing, total bond, booking date, DOB.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List, Optional

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_ROSTER_URL = "https://www.yellowstonecountymt.gov/sheriff/detention/dcsearch.asp"

_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def _text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _parse_value(raw: str) -> int:
    token = raw.strip()
    if token.isdigit():
        return int(token)
    lowered = token.lower()
    if lowered not in _WORDS:
        raise ValueError(f"Unsupported Yellowstone prompt token: {token}")
    return _WORDS[lowered]


def _solve_prompt(page_html: str) -> str:
    match = re.search(r'<label for="Answer"[^>]*>([^<]+)</label>', page_html)
    if not match:
        raise ValueError("Yellowstone verification prompt not found")
    label = _text(match.group(1))
    expr = label.split("=")[0].strip()
    parts = expr.split()
    if len(parts) != 3:
        raise ValueError(f"Unexpected Yellowstone prompt: {label}")
    left, op, right = _parse_value(parts[0]), parts[1], _parse_value(parts[2])
    if op == "+":
        return str(left + right)
    if op == "-":
        return str(left - right)
    raise ValueError(f"Unsupported Yellowstone operator: {op}")


def _parse_full_roster(page_html: str) -> List[Dict]:
    table_match = re.search(
        r'<table class="table table-striped _table-sm caption-top data-table">(.*?)</table>',
        page_html, re.IGNORECASE | re.DOTALL)
    if not table_match:
        return []
    rows: List[Dict] = []
    for row_html in re.findall(r"<tr>(.*?)</tr>", table_match.group(1), re.IGNORECASE | re.DOTALL):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.IGNORECASE | re.DOTALL)
        if len(cells) != 8:
            continue
        rows.append({
            "last_name": _text(cells[0]), "first_name": _text(cells[1]),
            "middle_name": _text(cells[2]), "jacket_number": _text(cells[3]),
            "housing_unit": _text(cells[4]), "total_bond": _text(cells[5]),
            "booking_date": _text(cells[6]), "date_of_birth": _text(cells[7]),
        })
    return rows


def _norm_dt(raw: Optional[str]) -> Optional[str]:
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%dT12:00:00Z" if fmt == "%m/%d/%Y" else "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def fetch(source) -> AdapterResult:
    url = source["source_url"] or _ROSTER_URL
    _assert_authorized(url)
    pulled_at = datetime.now(timezone.utc).isoformat()
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": url,
    }
    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        page_html = client.get(url, headers=headers).text
        answer = _solve_prompt(page_html)
        response = client.post(url, data={"ViewFullRoster": "True", "Answer": answer, "action": "Search"},
                               headers=headers)
        response.raise_for_status()
    rows = _parse_full_roster(response.text)
    records: List[Dict] = []
    for row in rows:
        last = (row["last_name"] or "").strip()
        first = (row["first_name"] or "").strip()
        middle = (row["middle_name"] or "").strip()
        jacket = (row["jacket_number"] or "").strip()
        identity = f"yellowstone|{last}|{first}|{middle}|{jacket}"
        records.append({
            "state": "MT",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "id": identity,
            "inmate_id": jacket or None,
            "booking_number": jacket or f"YSN-{identity}",
            "source_updated_at": pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at,
            "visibility": "public",
            "full_name": f"{last.title()}, {' '.join(p.title() for p in [first, middle] if p)}".strip(", "),
            "first_name": first.title(),
            "last_name": last.title(),
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": _norm_dt(row["booking_date"]) or (pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at),
            "release_date": None,
            "charges": [{"source_id": "chg-0", "description": "Charge details available on the official Yellowstone County inmate page.", "statute": None, "severity": None}],
            "bonds": ([{"source_id": "bond-0", "amount": float(re.sub(r"[^0-9.]", "", row["total_bond"]) or 0),
                        "type": "total", "status": "set"}] if row.get("total_bond") else []),
            "bond_amount": None,
            "status": "in_custody",
            "mugshot_url": None,
            "notes": row.get("housing_unit") or None,
        })
    return AdapterResult(source, records)
