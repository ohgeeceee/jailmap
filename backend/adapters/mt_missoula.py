"""Missoula County MT jail roster adapter.

Port of /root/montanablotter/services/ingestion/fetchers/missoula_inmate.py.
ASP.NET WebForms portal: GET the page, extract hidden fields, POST a
__doPostBack to "show all inmates", then parse the tab-separated text
stream (6-column rows) using the same line grammar as production.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List, Optional

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_URL = "https://webapps.missoulacounty.us/jailroster/Inmates"


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
        text = unescape("".join(self._parts)).replace("\xa0", " ").replace("\r", "\n")
        return re.sub(r"\n{3,}", "\n\n", text)


def _text_lines(page_html: str) -> List[str]:
    parser = _TextExtractor()
    parser.feed(page_html)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in parser.text().splitlines()]
    return [ln for ln in lines if ln]


def _hidden_fields(page_html: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for match in re.finditer(r"<input\b[^>]*>", page_html, re.IGNORECASE):
        tag = match.group(0)
        if not re.search(r'type="hidden"', tag, re.IGNORECASE):
            continue
        name = re.search(r'name="([^"]+)"', tag, re.IGNORECASE)
        if not name:
            continue
        value = re.search(r'value="([^"]*)"', tag, re.IGNORECASE)
        fields[unescape(name.group(1))] = unescape(value.group(1)) if value else ""
    return fields


def _is_name_line(line: str) -> bool:
    if "," not in line or line.upper() != line:
        return False
    return bool(re.match(r"^[A-Z' .-]+,\s*[A-Z' .-]+$", line))


def _norm_dt(raw: str) -> Optional[str]:
    raw = (raw or "").strip()
    if not raw:
        return None
    raw = re.sub(r"\b(am|pm)\b", lambda m: m.group(1).upper(), raw, flags=re.IGNORECASE)
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def fetch(source) -> AdapterResult:
    url = source["source_url"] or _URL
    _assert_authorized(url)
    pulled_at = datetime.now(timezone.utc).isoformat()
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": url,
    }
    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        page_html = response.text
        payload = _hidden_fields(page_html)
        if "__VIEWSTATE" in payload:
            payload.update({"__EVENTTARGET": "ctl00$MainContent$li9", "__EVENTARGUMENT": "", "__LASTFOCUS": ""})
            all_response = client.post(url, data=payload, headers=headers)
            all_response.raise_for_status()
            page_html = all_response.text

    lines = _text_lines(page_html)
    records: List[Dict] = []
    in_list = False
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("Current Inmate List for Today:"):
            in_list = True
            idx += 1
            continue
        if in_list and line.startswith("© "):
            break
        if not in_list:
            idx += 1
            continue
        if line in {
            "For details on an inmates charges or court schedule, please use the buttons to access that information.",
            "Name Age Booking ID Global/Jacket No Booking Date Charge Details",
        } or line in {"Name", "Age", "Booking ID", "Global/Jacket No", "Booking Date", "Charge Details"}:
            idx += 1
            continue
        if not _is_name_line(line):
            idx += 1
            continue

        name = line.title()
        # Variant A: six fields on separate lines (age, booking_id, jacket,
        # booking_date, "Charges").
        age_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        bid_line = lines[idx + 2] if idx + 2 < len(lines) else ""
        jacket_line = lines[idx + 3] if idx + 3 < len(lines) else ""
        bdate_line = lines[idx + 4] if idx + 4 < len(lines) else ""
        charges_line = lines[idx + 5] if idx + 5 < len(lines) else ""
        if (re.fullmatch(r"\d{1,3}", age_line)
                and re.fullmatch(r"\d{4}-\d{8}", bid_line)
                and re.fullmatch(r"\d+", jacket_line)
                and _norm_dt(bdate_line)
                and charges_line == "Charges"):
            booking_number = bid_line
            records.append({
                "state": "MT",
                "county": source["county"],
                "facility": source["facility_name"],
                "source_url": source["source_url"],
                "source_type": "custom_html",
                "pulled_at": pulled_at,
                "source_id": booking_number,
                "inmate_id": jacket_line,
                "booking_number": booking_number,
                "full_name": name,
                "first_name": name.split(", ", 1)[1] if ", " in name else "",
                "last_name": name.split(", ", 1)[0],
                "dob": None,
                "age": int(age_line),
                "sex": None,
                "race": None,
                "booking_date": _norm_dt(bdate_line),
                "release_date": None,
                "charges": [{"source_id": "chg-0", "description": "Charge details available on the official Missoula County inmate portal.", "statute": None, "severity": None}],
                "bonds": [],
                "bond_amount": None,
                "status": "in_custody",
                "mugshot_url": None,
                "source_updated_at": pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at,
                "visibility": "public",
                "notes": None,
            })
            idx += 6
            continue
        # Variant B: all six fields packed on one meta line.
        meta_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        match = re.match(
            r"^(?P<age>\d{1,3})\s+"
            r"(?P<booking_id>\d{4}-\d{8})\s+"
            r"(?P<jacket>\d+)\s+"
            r"(?P<booking_date>\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)"
            r"(?:\s+Charges)?$",
            meta_line,
        )
        if not match:
            idx += 1
            continue
        booking_number = match.group("booking_id")
        records.append({
            "state": "MT",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "source_id": booking_number,
            "inmate_id": match.group("jacket"),
            "booking_number": booking_number,
            "full_name": name,
            "first_name": name.split(", ", 1)[1] if ", " in name else "",
            "last_name": name.split(", ", 1)[0],
            "dob": None,
            "age": int(match.group("age")),
            "sex": None,
            "race": None,
            "booking_date": _norm_dt(match.group("booking_date")),
            "release_date": None,
            "charges": [{"source_id": "chg-0", "description": "Charge details available on the official Missoula County inmate portal.", "statute": None, "severity": None}],
            "bonds": [],
            "bond_amount": None,
            "status": "in_custody",
            "mugshot_url": None,
            "source_updated_at": pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at,
            "visibility": "public",
            "notes": None,
        })
        idx += 2
    return AdapterResult(source, records)
