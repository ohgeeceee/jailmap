from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_clatsop_county():
    """Scrape Clatsop County jail roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://apps.clatsopcounty.gov/jail/', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        
        text = page.inner_text('body')
        browser.close()
        return text


def parse(source) -> AdapterResult:
    """Parse Clatsop County HTML inmate roster (div-based table)."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    text = _scrape_clatsop_county()
    
    if not text:
        return AdapterResult(source, [])
    
    # Parse the text content
    # Pattern: NAME\tBOOKED\tSCHEDULED RELEASE\tLOCATION
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if line.startswith('Inmate Name') or line.startswith('Search') or line.startswith('Previous') or line.startswith('Next'):
            continue
        
        # Skip pagination lines
        if line.isdigit() or line in ['1', '2', '3', '4', '5', '…', '8']:
            continue
        
        # Skip footer lines
        if 'In Custody' in line and 'Electronic Monitoring' in line:
            continue
        
        # Split by tab
        parts = line.split('\t')
        if len(parts) < 4:
            continue
        
        name = parts[0].strip()
        booked = parts[1].strip()
        scheduled_release = parts[2].strip()
        location = parts[3].strip()
        
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
            "state": "OR",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "booking_number": None,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": booked,
            "release_date": scheduled_release if scheduled_release else None,
            "charges": [],
            "bond_amount": None,
            "status": "in_custody" if "Custody" in location else "other",
            "mugshot_url": None,
            "notes": f"Location: {location}",
        })
    
    return AdapterResult(source, records)
