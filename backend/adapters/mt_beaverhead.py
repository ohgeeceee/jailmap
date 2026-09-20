"""Beaverhead County MT jail roster adapter.

PDF roster: https://beaverheadcountymt.gov/wp-content/uploads/2026/03/Jail-Roster.pdf
Text-based PDF. Each inmate starts with a header line:
  Book#: 26BK00095 Name: AMOS,NICHOLASC NameID: 21693 Rel.Dt: **/**/**
Followed by statute lines with charges.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List

import httpx
import pdfplumber
from io import BytesIO

from backend.adapters.idaho import AdapterResult, _assert_authorized

_URL = "https://beaverheadcountymt.gov/wp-content/uploads/2026/03/Jail-Roster.pdf"

# Pattern for inmate header line
# Format: Book#: 26BK00095 Name: AMOS,NICHOLASC NameID: 21693 Rel.Dt: **/**/**
_INMATE_HEADER_RE = re.compile(
    r'Book#:\s*(\S+)\s+Name:\s*(\S+)\s+NameID:\s*(\S+)\s+Rel\.Dt:\s*(\S+)'
)

# Pattern for statute lines (charges)
# Format: 45-5-215(2)(a)[1st] StrangulationofPartnerorFamily BCSO DC-1-2026- 03/09/26 189
_STATUTE_RE = re.compile(
    r'^(\S+)\s+(.+?)\s+(\w+)\s+(\S+)\s+(\d{2}/\d{2}/\d{2})\s+(\d+)$'
)


def _parse_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw or raw == "**/**/**":
        return None
    for fmt in ("%m/%d/%y", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%dT12:00:00Z")
        except ValueError:
            continue
    return None


def _parse_pdf(pdf_bytes: bytes) -> List[Dict]:
    entries = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = _INMATE_HEADER_RE.search(line)
        if m:
            if current:
                entries.append(current)
            booking_number = m.group(1)
            name = m.group(2)
            if "," in name:
                last, first = [p.strip() for p in name.split(",", 1)]
            else:
                parts = name.split()
                first = parts[0] if parts else ""
                last = " ".join(parts[1:]) if len(parts) > 1 else ""

            current = {
                "booking_number": booking_number,
                "first_name": first,
                "last_name": last,
                "name_id": m.group(3),
                "release_date": _parse_date(m.group(4)),
                "charges": [],
            }
        elif current is not None:
            # Try to parse as statute line
            sm = _STATUTE_RE.match(line)
            if sm:
                statute = sm.group(1)
                description = sm.group(2)
                agency = sm.group(3)
                case_num = sm.group(4)
                date = sm.group(5)
                days = sm.group(6)
                current["charges"].append({
                    "statute": statute,
                    "description": description[:2000],
                    "agency": agency,
                    "case_number": case_num,
                    "date": _parse_date(date),
                    "days": int(days) if days.isdigit() else None,
                })
            elif not line.startswith("Inmate") and not line.startswith("Statute"):
                # Raw charge line
                current["charges"].append({
                    "statute": None,
                    "description": line[:2000],
                    "agency": None,
                    "case_number": None,
                    "date": None,
                    "days": None,
                })

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
        release_date = entry["release_date"]
        records.append({
            "state": "MT",
            "county": "Beaverhead",
            "facility": source.get("facility_name", "Beaverhead County Jail"),
            "source_url": url,
            "source_type": "pdf_roster",
            "pulled_at": pulled_at,
            "source_id": entry["booking_number"],
            "inmate_id": entry["name_id"],
            "booking_number": entry["booking_number"],
            "source_updated_at": release_date or pulled_at,
            "visibility": "public",
            "full_name": f"{entry['first_name']} {entry['last_name']}".strip(),
            "first_name": entry["first_name"],
            "last_name": entry["last_name"],
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": release_date or pulled_at,
            "release_date": release_date,
            "charges": [{"source_id": f"CH-{j:03d}", "description": c["description"][:2000],
                         "statute": c["statute"], "severity": None}
                        for j, c in enumerate(entry["charges"])],
            "bond_amount": None,
            "bonds": [],
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
