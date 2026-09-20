from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_benton_county():
    """Scrape Benton County jail roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://sheriff.bentoncountyor.gov/adult-in-custody-roster/', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        
        content = page.content()
        browser.close()
        return content


def parse(source) -> AdapterResult:
    """Parse Benton County HTML inmate roster (accordion format)."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    content = _scrape_benton_county()
    
    if not content:
        return AdapterResult(source, [])
    
    # Parse accordion items
    # Pattern: <button class="accordion-button collapsed" ...>DATE - NAME [COUNTY]</button>
    accordion_buttons = re.findall(
        r'<button[^>]*class="[^"]*accordion-button[^"]*"[^>]*>(.*?)</button>',
        content,
        re.DOTALL | re.IGNORECASE
    )
    
    for button_text in accordion_buttons:
        clean_text = re.sub(r'<[^>]+>', '', button_text).strip()
        
        # Parse: "DATE - NAME [COUNTY]"
        match = re.match(r'(\w+ \d{1,2}, \d{4})\s*-\s*(.+?)\s*\[(\w+)\]', clean_text)
        if not match:
            continue
        
        date_str = match.group(1)
        name = match.group(2).strip()
        county = match.group(3).strip()
        
        # Parse name: "FIRST MIDDLE LAST"
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
        else:
            first_name = name
            last_name = ""
        
        records.append({
            "state": "OR",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "source_updated_at": pulled_at,
            "booking_number": None,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": date_str,
            "release_date": None,
            "charges": [],
            "bond_amount": None,
            "status": "in_custody", "visibility": "public",
            "mugshot_url": None,
            "notes": f"County: {county}",
        })
    
    return AdapterResult(source, records)
