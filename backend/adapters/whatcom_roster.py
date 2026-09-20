from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_whatcom_county():
    """Scrape Whatcom County jail roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://www.whatcomcounty.us/250/Jail-Roster-Search', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        
        text = page.inner_text('body')
        browser.close()
        return text


def parse(source) -> AdapterResult:
    """Parse Whatcom County jail roster."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    text = _scrape_whatcom_county()
    
    if not text:
        return AdapterResult(source, [])
    
    # Parse the text content
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if line.startswith('Name') and line.endswith('Name ID'):
            continue
        
        # Split by tab
        parts = line.split('\t')
        if len(parts) < 6:
            continue
        
        name = parts[0].strip()
        booking_date = parts[1].strip()
        facility = parts[2].strip()
        floor = parts[3].strip()
        cell = parts[4].strip()
        name_id = parts[5].strip()
        
        # Skip if not a valid name
        if not name or not name[0].isalpha():
            continue
        
        # Parse name: "LAST, FIRST MIDDLE"
        if "," in name:
            parts = name.split(",", 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        records.append({
            "state": "WA",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "source_updated_at": pulled_at,
            "inmate_id": name_id,
            "booking_number": name_id,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "release_date": None,
            "charges": [],
            "bond_amount": None,
            "status": "in_custody", "visibility": "public",
            "mugshot_url": None,
            "notes": f"Facility: {facility}, Floor: {floor}, Cell: {cell}",
        })
    
    return AdapterResult(source, records)
