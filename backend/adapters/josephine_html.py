from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _search_josephine_county(name: str = None, in_custody: bool = True):
    """Search Josephine County jail roster using Playwright."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://jailviewer.josephinecounty.gov/NewWorld.InmateInquiry/OR0170000', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(2000)
        
        # Fill name if provided
        if name:
            name_input = page.locator('#uxName')
            name_input.fill(name)
        
        # Check "In Custody" if requested
        if in_custody:
            in_custody_checkbox = page.locator('#uxInCustody')
            if in_custody_checkbox:
                in_custody_checkbox.check()
        
        # Click Search
        search_button = page.locator('input[type="submit"][value="Search"]')
        search_button.click()
        page.wait_for_timeout(3000)
        
        content = page.content()
        browser.close()
        return content


def parse(source) -> AdapterResult:
    """Parse Josephine County HTML inmate roster (NewWorld InmateInquiry)."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    # Search with "In Custody" checked to get current inmates
    content = _search_josephine_county(in_custody=True)
    
    if not content:
        return AdapterResult(source, [])
    
    # Parse table rows
    rows = re.findall(r'<tr>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
    
    for row in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
        clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        
        # Skip header rows
        if not clean_cells or clean_cells[0] == 'Name':
            continue
        
        # Parse row: Name, Subject Number, In Custody, Gender, Height, Weight, Multiple Bookings, Housing Facility
        if len(clean_cells) < 8:
            continue
        
        name = clean_cells[0]
        subject_number = clean_cells[1]
        in_custody = clean_cells[2]
        gender = clean_cells[3]
        height = clean_cells[4]
        weight = clean_cells[5]
        multiple_bookings = clean_cells[6]
        housing_facility = clean_cells[7]
        
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
            "source_updated_at": pulled_at,
            "inmate_id": subject_number,
            "booking_number": subject_number,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": gender,
            "race": None,
            "booking_date": None,
            "release_date": None,
            "charges": [],
            "bond_amount": None,
            "status": "in_custody", "visibility": "public" if in_custody else "released",
            "mugshot_url": None,
            "notes": f"Height: {height}, Weight: {weight}, Multiple: {multiple_bookings}, Housing: {housing_facility}",
        })
    
    return AdapterResult(source, records)
