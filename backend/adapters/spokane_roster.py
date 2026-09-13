from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _scrape_spokane_county():
    """Scrape Spokane County inmate roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://cp.spokanecounty.org/detentionservices/inmateroster.aspx', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)
        
        # Select 100 names per page
        page.select_option('select[name="roster_length"]', '100')
        page.wait_for_timeout(2000)
        
        text = page.inner_text('body')
        browser.close()
        return text


def parse(source) -> AdapterResult:
    """Parse Spokane County inmate roster."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    text = _scrape_spokane_county()
    
    if not text:
        return AdapterResult(source, [])
    
    # Parse the text content
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines
        if line.startswith('Inmate Name') and line.endswith('Total Bond'):
            continue
        
        # Skip pagination lines
        if line.startswith('Showing') or line.startswith('First') or line.startswith('Previous') or line.startswith('Next') or line.startswith('Last'):
            continue
        
        # Split by tab
        parts = line.split('\t')
        if len(parts) < 5:
            continue
        
        name = parts[0].strip()
        book_number = parts[1].strip()
        status = parts[2].strip()
        bondable = parts[3].strip()
        total_bond = parts[4].strip()
        
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
        
        # Parse bond amount
        bond_amount = None
        if total_bond and total_bond != '$0.00':
            try:
                bond_amount = float(total_bond.replace('$', '').replace(',', ''))
            except ValueError:
                pass
        
        records.append({
            "state": "WA",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "inmate_id": book_number,
            "booking_number": book_number,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": None,
            "release_date": None,
            "charges": [],
            "bond_amount": bond_amount,
            "status": "in_custody",
            "mugshot_url": None,
            "notes": f"Status: {status}, Bondable: {bondable}",
        })
    
    return AdapterResult(source, records)
