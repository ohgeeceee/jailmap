from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_umatilla_county():
    """Scrape Umatilla County arrests page using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://ucso.citizenrims.com/', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)
        
        text = page.inner_text('body')
        browser.close()
        return text


def parse(source) -> AdapterResult:
    """Parse Umatilla County CitizenRIMS arrests page."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    text = _scrape_umatilla_county()
    
    if not text:
        return AdapterResult(source, [])
    
    # Parse the text content
    # Pattern: Name\nDate Arrested: DATE at TIME\nCase Number: CASE\nCharge(s): CHARGES
    blocks = re.split(r'\n\n', text)
    
    for block in blocks:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        
        # Skip blocks that don't start with a name
        if not lines or 'Date Arrested:' not in block:
            continue
        
        # First line is the name
        name = lines[0].strip()
        
        # Parse date arrested
        date_match = re.search(r'Date Arrested:\s+(\d{1,2}/\d{1,2}/\d{4})\s+at\s+(\d{1,2}:\d{2}\s*[AP]M)', block)
        arrest_date = date_match.group(1) if date_match else None
        arrest_time = date_match.group(2) if date_match else None
        
        # Parse case number
        case_match = re.search(r'Case Number:\s+(\S+)', block)
        case_number = case_match.group(1) if case_match else None
        
        # Parse charges
        charge_match = re.search(r'Charge\(s\):\s+(.+?)(?:\n\n|$)', block, re.DOTALL)
        charges_text = charge_match.group(1).strip() if charge_match else ""
        
        # Clean up charges - remove "20 Records Found" and similar
        charges_text = re.sub(r'\d+\s*Records?\s*Found', '', charges_text).strip()
        
        # Parse name: "FIRST MIDDLE LAST" (no comma)
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
        else:
            first_name = name
            last_name = ""
        
        # Parse charges into list
        charges = []
        if charges_text:
            # Split by comma or semicolon
            charge_list = re.split(r'[,;]', charges_text)
            for i, charge in enumerate(charge_list):
                charge = charge.strip()
                # Skip empty charges and "20 Records Found" type text
                if charge and not re.match(r'^\d+\s*Records?\s*Found$', charge):
                    charges.append({
                        "source_id": f"c{i+1}",
                        "description": charge,
                        "statute": None,
                        "severity": None,
                    })
        
        records.append({
            "state": "OR",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "source_updated_at": pulled_at,
            "inmate_id": case_number,
            "booking_number": case_number,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": arrest_date,
            "release_date": None,
            "charges": charges or [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}],
            "bond_amount": None,
            "status": "in_custody", "visibility": "public",
            "mugshot_url": None,
            "notes": f"Arrest Time: {arrest_time}",
        })
    
    return AdapterResult(source, records)
