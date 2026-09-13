from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_cuyahoga_county():
    """Scrape Cuyahoga County jail roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('http://74.218.167.200/p2c/jailinmates.aspx', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        
        text = page.inner_text('body')
        browser.close()
        return text


def parse(source) -> AdapterResult:
    """Parse Cuyahoga County jail roster."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    text = _scrape_cuyahoga_county()
    
    if not text:
        return AdapterResult(source, [])
    
    # Parse the text content
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if 'Inmate Inquiry' in line or 'Last Name' in line:
            continue
        
        # Look for inmate data patterns
        if len(line) > 5 and line[0].isalpha():
            records.append({
                "state": "OH",
                "county": source["county"],
                "facility": source["facility_name"],
                "source_url": source["source_url"],
                "source_type": "custom_html",
                "pulled_at": pulled_at,
                "inmate_id": None,
                "booking_number": None,
                "full_name": line,
                "first_name": "",
                "last_name": line,
                "dob": None,
                "age": None,
                "sex": None,
                "race": None,
                "booking_date": None,
                "release_date": None,
                "charges": [],
                "bond_amount": None,
                "status": "in_custody",
                "mugshot_url": None,
                "notes": None,
            })
    
    return AdapterResult(source, records)
