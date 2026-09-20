from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_maricopa_county():
    """Scrape Maricopa County jail roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://portal.mobileso.com/mcso/jail/jp_ci_c.asp', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        
        text = page.inner_text('body')
        browser.close()
        return text


def parse(source) -> AdapterResult:
    """Parse Maricopa County jail roster."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    text = _scrape_maricopa_county()
    
    if not text:
        return AdapterResult(source, [])
    
    # Parse the text content
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if line.startswith('Booking') and line.endswith('Expected Release'):
            continue
        
        # Split by tab
        parts = line.split('\t')
        if len(parts) < 10:
            continue
        
        booking_number = parts[0].strip()
        name = parts[1].strip()
        race = parts[2].strip()
        sex = parts[3].strip()
        dob = parts[4].strip()
        status = parts[5].strip()
        age = parts[6].strip()
        booking_date = parts[7].strip()
        arrival_date = parts[8].strip()
        expected_release = parts[9].strip()
        
        # Skip if not a valid name
        if not name or not name[0].isalpha():
            continue
        
        # Parse name: "LAST, FIRST"
        if "," in name:
            parts = name.split(",", 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        records.append({
            "state": "AZ",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "source_updated_at": pulled_at,
            "inmate_id": booking_number,
            "booking_number": booking_number,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "age": int(age) if age.isdigit() else None,
            "sex": sex,
            "race": race,
            "booking_date": booking_date,
            "release_date": expected_release if expected_release else None,
            "charges": [],
            "bond_amount": None,
            "status": "in_custody", "visibility": "public" if status == "Booked" else status.lower(),
            "mugshot_url": None,
            "notes": f"Arrival: {arrival_date}",
        })
    
    return AdapterResult(source, records)
