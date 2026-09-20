from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _get_canyon_county_token_and_cookies():
    """Get the anti-forgery token and cookies from Canyon County website."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://jailroster.canyoncounty.id.gov/', wait_until='networkidle')
        page.wait_for_timeout(2000)
        
        content = page.content()
        token_match = re.search(r'<input id="RequestVerificationToken" type="hidden" value="([^"]+)"', content)
        token = token_match.group(1) if token_match else None
        
        cookies = context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        
        browser.close()
        return token, cookie_dict


def _fetch_canyon_county_page(token: str, cookies: dict, letter: str = None, name: str = None):
    """Fetch a page from Canyon County API."""
    import httpx
    
    headers = {
        'User-Agent': 'jailmap/1.0 (+https://jailmap.com; contact ops@jailmap.com)',
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {'__RequestVerificationToken': token}
    if letter:
        data['letter'] = letter
        url = 'https://jailroster.canyoncounty.id.gov/Roster/GetListByLetter'
    elif name:
        data['name'] = name
        url = 'https://jailroster.canyoncounty.id.gov/Roster/GetListByName'
    else:
        return None
    
    r = httpx.post(url, data=data, headers=headers, cookies=cookies, follow_redirects=True)
    if r.status_code == 200:
        return r.text
    return None


def parse(source) -> AdapterResult:
    """Parse Canyon County HTML inmate roster (ASP.NET Blazor with anti-forgery token)."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    # Get token and cookies
    try:
        token, cookies = _get_canyon_county_token_and_cookies()
    except Exception:
        return AdapterResult(source, [])
    
    if not token:
        return AdapterResult(source, [])
    
    # Fetch all letters A-Z
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        html = _fetch_canyon_county_page(token, cookies, letter=letter)
        if not html:
            continue
        
        # Parse inmate rows
        # Pattern: <div class="row inmate_row" id="row_0" data-namenum="..." data-inmatename="...">
        inmate_divs = re.findall(
            r'<div class="row inmate_row"[^>]*data-namenum="(\d+)"[^>]*data-inmatename="([^"]+)"',
            html
        )
        
        for name_num, inmate_name in inmate_divs:
            # Parse name: "FIRST MIDDLE LAST" (uppercase)
            name_parts = inmate_name.strip().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            else:
                first_name = inmate_name
                last_name = ""
            
            # Extract charges for this inmate
            charges = []
            # Find the charges table for this inmate
            charge_section = re.search(
                rf'<div class="row inmate_row"[^>]*data-namenum="{name_num}"[^>]*>.*?<tbody class="charges">(.*?)</tbody>',
                html,
                re.DOTALL
            )
            if charge_section:
                charge_rows = re.findall(r'<td>([^<]+)</td>', charge_section.group(1))
                for i, charge in enumerate(charge_rows):
                    charges.append({
                        "source_id": f"c{i+1}",
                        "description": charge.strip(),
                        "statute": None,
                        "severity": None,
                    })
            
            records.append({
                "state": "ID",
                "county": source["county"],
                "facility": source["facility_name"],
                "source_url": source["source_url"],
                "source_type": "custom_html",
                "source_updated_at": pulled_at,
                "inmate_id": name_num,
                "booking_number": None,
                "full_name": f"{first_name} {last_name}".strip(),
                "first_name": first_name,
                "last_name": last_name,
                "dob": None,
                "age": None,
                "sex": None,
                "race": None,
                "booking_date": None,
                "release_date": None,
                "charges": charges or [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}],
                "bond_amount": None,
                "status": "in_custody", "visibility": "public",
                "mugshot_url": f"https://jailroster.canyoncounty.id.gov/image?nameNum={name_num}.thumb",
                "notes": None,
            })
    
    return AdapterResult(source, records)
