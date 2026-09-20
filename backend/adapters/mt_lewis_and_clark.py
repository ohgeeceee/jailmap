"""Lewis and Clark County MT jail roster adapter.

PDF roster: https://www.lccountymt.gov/files/assets/county/v/232/sheriff/documents/jail_roster.pdf
Text-based PDF. Each inmate record starts with a line:
  Name Age Sex Booking Date & Time Booking # Hold Reasons
Then multiline charge text.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List

import httpx
import pdfplumber
from io import BytesIO

from backend.adapters.idaho import AdapterResult, _assert_authorized

_URL = "https://www.lccountymt.gov/files/assets/county/v/232/sheriff/documents/jail_roster.pdf"

# Pattern for inmate record start
# Format: ALDEN, BRANDON 42 Male 09/09/26 01:31 26-01659
_INMATE_RE = re.compile(
    r'^([A-Z][A-Z\s,]+?)\s+(\d{1,3})\s+(Male|Female)\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s+(\S+)'
)

_DATE_FORMATS = ("%m/%d/%y %H:%M", "%m/%d/%Y %H:%M")


def _parse_datetime(date_str: str, time_str: str) -> str | None:
    raw = f"{date_str} {time_str}".strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def _parse_pdf(pdf_bytes: bytes) -> List[Dict]:
    entries = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = text.splitlines()
    current = None
    for line in lines:
        line = line.strip()
        if not line or line == "Name Age Sex Booking Date & Time Booking # Hold Reasons":
            continue

        m = _INMATE_RE.match(line)
        if m:
            if current:
                entries.append(current)
            name_part = m.group(1).strip()
            if "," in name_part:
                last, first = [p.strip() for p in name_part.split(",", 1)]
            else:
                parts = name_part.split()
                first = parts[0] if parts else ""
                last = " ".join(parts[1:]) if len(parts) > 1 else ""

            current = {
                "first_name": first,
                "last_name": last,
                "age": int(m.group(2)),
                "sex": m.group(3),
                "booking_date": _parse_datetime(m.group(4), m.group(5)),
                "booking_number": m.group(6),
                "charges_raw": [],
            }
            # Check for inline charges after booking number
            remainder = line[m.end():].strip()
            if remainder:
                current["charges_raw"].append(remainder)
        elif current is not None:
            current["charges_raw"].append(line)

    if current:
        entries.append(current)
    return entries


def fetch(source) -> AdapterResult:
    url = source.get("source_url") or _URL
    _assert_authorized(url)
    pulled_at = datetime.now(timezone.utc).isoformat()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
        "Accept": "application/pdf,application/octet-stream",
    }
    with httpx.Client(timeout=60, follow_redirects=True, verify=False) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        pdf_bytes = response.content

    entries = _parse_pdf(pdf_bytes)
    records = []
    for entry in entries:
        records.append({
            "state": "MT",
            "county": "Lewis and Clark",
            "facility": source.get("facility_name", "Lewis and Clark County Detention Center"),
            "source_url": url,
            "source_type": "pdf_roster",
            "pulled_at": pulled_at,
            "source_id": entry["booking_number"],
            "booking_number": entry["booking_number"],
            "source_updated_at": entry["booking_date"] or pulled_at,
            "visibility": "public",
            "full_name": f"{entry['first_name']} {entry['last_name']}".strip(),
            "first_name": entry["first_name"],
            "last_name": entry["last_name"],
            "dob": None,
            "age": entry["age"],
            "sex": entry["sex"],
            "race": None,
            "booking_date": entry["booking_date"],
            "release_date": None,
            "charges": [{"source_id": f"CH-{j:03d}", "description": c[:2000],
                         "statute": None, "severity": None}
                        for j, c in enumerate(entry["charges_raw"])],
            "bond_amount": None,
            "bonds": [],
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
