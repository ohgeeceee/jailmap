"""Florida county jail roster adapters.

Handles multiple vendor types:
- SmartWEB (CTS-America): Bradford, Escambia, Gadsden, Glades, Hamilton, Putnam, Sumter, Suwannee
- Inmate search forms: Alachua, Brevard, Clay, Collier, etc.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class AdapterResult:
    def __init__(self, source, records):
        self.source = source
        self.records = records


def fetch_html(url: str) -> str:
    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        return client.get(url, headers=HEADERS).text


def smartweb_parse(html: str, source_url: str, county: str = "", facility: str = "") -> List[Dict]:
    """Parse SmartWEB Jail.aspx."""
    records = []
    now = datetime.now(timezone.utc).isoformat()
    
    for row_match in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE):
        row = row_match.group(1)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
        if len(cells) < 3:
            continue
        
        cell_texts = [re.sub(r"<[^>]+>", " ", c).strip() for c in cells]
        cell_texts = [re.sub(r"\s+", " ", t).strip() for t in cell_texts]
        
        name = cell_texts[0] if cell_texts else ""
        if not name or len(name) < 3 or name.lower() == "name":
            continue
        
        if "," in name:
            parts = name.split(",", 1)
            first_name = parts[1].strip()
            last_name = parts[0].strip()
        else:
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        booking_date = cell_texts[1] if len(cell_texts) > 1 else ""
        charges_text = cell_texts[2] if len(cell_texts) > 2 else ""
        
        charges = [{"source_id": f"c{i+1}", "description": c.strip(), "statute": None, "severity": None}
                   for i, c in enumerate(re.split(r"[,;]", charges_text)) if c.strip()]
        if not charges:
            charges = [{"source_id": "c1", "description": "Unknown", "statute": None, "severity": None}]
        
        records.append({
            "state": "FL", "county": county, "facility": facility,
            "source_url": source_url, "source_type": "smartweb",
            "pulled_at": now, "full_name": name,
            "first_name": first_name, "last_name": last_name,
            "booking_date": booking_date, "charges": charges, "status": "in_custody",
        })
    
    return records


def inmate_search_parse(html: str, source_url: str, county: str = "", facility: str = "") -> List[Dict]:
    """Parse simple inmate search results page."""
    records = []
    now = datetime.now(timezone.utc).isoformat()
    
    # Look for name patterns — booking number patterns
    # Common format: "Last, First | Date | Charges"
    for match in re.finditer(
        r"([A-Z][A-Za-z]+),\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s*\n?\s*(\d{1,2}/\d{1,2}/\d{4})?\s*\n?\s*([^\n]+)",
        html
    ):
        last_name = match.group(1)
        first_name = match.group(2)
        booking_date = match.group(3) or ""
        charges_text = match.group(4) or ""
        
        if len(charges_text) < 3 or len(last_name) < 2:
            continue
        
        charges = [{"source_id": f"c{i+1}", "description": c.strip(), "statute": None, "severity": None}
                   for i, c in enumerate(re.split(r"[,;]", charges_text)) if c.strip()]
        if not charges:
            charges = [{"source_id": "c1", "description": "Unknown", "statute": None, "severity": None}]
        
        records.append({
            "state": "FL", "county": county, "facility": facility,
            "source_url": source_url, "source_type": "custom_html",
            "pulled_at": now, "full_name": f"{last_name}, {first_name}",
            "first_name": first_name, "last_name": last_name,
            "booking_date": booking_date, "charges": charges, "status": "in_custody",
        })
    
    return records


def smartweb_county(source: Dict[str, Any]) -> AdapterResult:
    """SmartWEB adapter."""
    url = source.get("source_url")
    county = source.get("county", "")
    facility = source.get("facility_name", f"{county} County Jail")
    
    try:
        html = fetch_html(url)
        records = smartweb_parse(html, url, county=county, facility=facility)
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def inmate_search_county(source: Dict[str, Any]) -> AdapterResult:
    """Simple inmate search adapter."""
    url = source.get("source_url")
    county = source.get("county", "")
    facility = source.get("facility_name", f"{county} County Jail")
    
    try:
        html = fetch_html(url)
        records = inmate_search_parse(html, url, county=county, facility=facility)
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


# Dispatch by county
FLORIDA_ADAPTERS = {
    # SmartWEB counties
    "Bradford": smartweb_county,
    "Escambia": smartweb_county,
    "Gadsden": smartweb_county,
    "Glades": smartweb_county,
    "Hamilton": smartweb_county,
    "Putnam": smartweb_county,
    "Sumter": smartweb_county,
    "Suwannee": smartweb_county,
    # Inmate search form counties (simple HTML)
    "Alachua": inmate_search_county,
    "Brevard": inmate_search_county,
    "Clay": inmate_search_county,
    "Collier": inmate_search_county,
    "Hernando": inmate_search_county,
    "Highlands": inmate_search_county,
    "Lake": inmate_search_county,
    "Lee": inmate_search_county,
    "Leon": inmate_search_county,
    "Manatee": inmate_search_county,
    "Marion": inmate_search_county,
    "Martin": inmate_search_county,
    "Okeechobee": inmate_search_county,
    "Orange": inmate_search_county,
    "Osceola": inmate_search_county,
    "Palm Beach": inmate_search_county,
    "Pasco": inmate_search_county,
    "Pinellas": inmate_search_county,
    "Polk": inmate_search_county,
    "St. Johns": inmate_search_county,
    "Santa Rosa": inmate_search_county,
    "Sarasota": inmate_search_county,
    "Seminole": inmate_search_county,
    "St. Lucie": inmate_search_county,
    "Volusia": inmate_search_county,
    "Washington": inmate_search_county,
}
