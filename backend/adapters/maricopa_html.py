from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _parse_maricopa_date(value: Optional[str]) -> Optional[str]:
    """Parse Maricopa date formats like '09/04/2026 23:24:17' or '09/04/2026'."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return value


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()


def parse(source) -> AdapterResult:
    """Parse Maricopa County MCSO Daily Jail Population Report.

    Source: https://portal.mobileso.com/mcso/jail/jp_ci_c.asp
    Returns a plain HTML table — no CAPTCHA, no JS rendering needed.
    """
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    html = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")

    # Extract report date from header
    report_date = None
    date_match = re.search(r"Charges as of (\d{1,2}/\d{1,2}/\d{4})", html)
    if date_match:
        report_date = date_match.group(1)

    # Find all inmate rows - both ctd and cdt classes
    row_pattern = re.compile(r'<tr class="ctd">(.*?)</tr>', re.DOTALL)

    for row_match in row_pattern.finditer(html):
        row_html = row_match.group(1)
        
        # Extract all td content
        td_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
        tds = td_pattern.findall(row_html)
        
        if len(tds) < 10:
            continue
        
        # Strip HTML from each td
        cells = [_strip_html(td) for td in tds]
        
        booking_number = cells[0]
        name = cells[1]
        race = cells[2].rstrip("*")
        sex = cells[3]
        dob = cells[4]
        status = cells[5]
        age = cells[6]
        booking_date = cells[7]
        arrival_date = cells[8]
        expected_release = cells[9]

        # Skip if not a valid booking number (12 digits: YYYYMMDDNNNN)
        if not re.match(r'^\d{12}$', booking_number):
            continue

        # Parse name: "LAST, FIRST" or "LAST, FIRST MIDDLE"
        first_name = ""
        last_name = ""
        if "," in name:
            parts = name.split(",", 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            parts = name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            elif parts:
                last_name = parts[0]

        # Parse DOB
        dob_parsed = None
        if dob:
            try:
                dt = datetime.strptime(dob, "%m/%d/%Y")
                dob_parsed = dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                pass

        records.append(
            {
                "state": "AZ",
                "county": source["county"],
                "facility": source["facility_name"],
                "source_url": source["source_url"],
                "source_type": "custom_html",
                "pulled_at": pulled_at,
                "inmate_id": booking_number,
                "booking_number": booking_number,
                "full_name": f"{first_name} {last_name}".strip(),
                "first_name": first_name,
                "last_name": last_name,
                "dob": dob_parsed,
                "age": int(age) if age.isdigit() else None,
                "sex": sex,
                "race": race,
                "booking_date": _parse_maricopa_date(booking_date),
                "release_date": _parse_maricopa_date(expected_release) if expected_release else None,
                "charges": [],
                "bond_amount": None,
                "status": "in_custody" if status.lower() == "booked" else status.lower(),
                "mugshot_url": None,
                "notes": f"Arrival: {arrival_date}" if arrival_date else None,
            }
        )

    return AdapterResult(source, records)
