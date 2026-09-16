"""Lake County MT jail roster adapter.

PDF roster: https://www.lakemt.gov/DocumentCenter/View/816/Jail_Roster-?bidId=
Text-based PDF (not table-based). Each inmate record starts with a line
containing name, jacket #, age, race, sex, days, booking date, agency.
Subsequent lines are charges.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List

import httpx
import pdfplumber
from io import BytesIO

from backend.adapters.idaho import AdapterResult, _assert_authorized

_URL = "https://www.lakemt.gov/DocumentCenter/View/816/Jail_Roster-?bidId="

# Pattern for the start of an inmate record
# Format: LAST, FIRST MIDDLE Jacket# Age Race Sex Days BookingDate Agency
_INMATE_RE = re.compile(
    r'^([A-Z][A-Z\s\-\',\.]+?)\s+(\d{2}-\d{3,4})\s+(\d{1,3})\s+([A-Z][a-z]+)\s+(Male|Female)\s+(\d{1,4})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z]{2,5})'
)


def _parse_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw:
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

    lines = text.splitlines()
    current = None
    for line in lines:
        line = line.strip()
        if not line:
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
                "jacket_number": m.group(2),
                "age": int(m.group(3)),
                "race": m.group(4),
                "sex": m.group(5),
                "days": int(m.group(6)),
                "booking_date": _parse_date(m.group(7)),
                "agency": m.group(8),
                "charges": [],
            }
        elif current is not None:
            # This is a charge line
            charge = line.strip()
            if charge and not charge.startswith("Charges"):
                current["charges"].append(charge)

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
    for i, entry in enumerate(entries):
        booking_number = f"LC-{entry['jacket_number']}-{i:04d}"
        records.append({
            "state": "MT",
            "county": "Lake",
            "facility": source.get("facility_name", "Lake County Jail"),
            "source_url": url,
            "source_type": "pdf_roster",
            "pulled_at": pulled_at,
            "source_id": booking_number,
            "inmate_id": None,
            "booking_number": booking_number,
            "source_updated_at": entry["booking_date"] or pulled_at,
            "visibility": "public",
            "full_name": f"{entry['first_name']} {entry['last_name']}".strip(),
            "first_name": entry["first_name"],
            "last_name": entry["last_name"],
            "dob": None,
            "age": entry["age"],
            "sex": entry["sex"],
            "race": entry["race"],
            "booking_date": entry["booking_date"],
            "release_date": None,
            "charges": [{"source_id": f"CH-{j:03d}", "description": c[:2000],
                         "statute": None, "severity": None}
                        for j, c in enumerate(entry["charges"])],
            "bond_amount": None,
            "bonds": [],
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
