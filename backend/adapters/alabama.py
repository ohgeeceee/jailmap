"""Alabama county jail roster adapters.

Each county has its own URL structure:
- Mobile: iframe from all.mobileso.com
- Jefferson: div-based roster.php
- Madison: SmartWEB portal
- Baldwin: search form
- Elmore: roster page
- Houston: roster page
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class AdapterResult:
    def __init__(self, source, records):
        self.source = source
        self.records = records


def fetch_html(url: str, timeout: int = 30) -> str:
    with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
        response = client.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text


def parse_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            continue
    return value


def split_name(full_name: str) -> tuple[str, str]:
    full_name = (full_name or "").strip()
    if not full_name:
        return ("Unknown", "")
    if "," in full_name:
        parts = [p.strip() for p in full_name.split(",", 1)]
        return (parts[1], parts[0]) if len(parts) > 1 else (parts[0], "")
    parts = full_name.split()
    if len(parts) >= 2:
        return (parts[0], " ".join(parts[1:]))
    return (parts[0], "")


def clean_html_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"&\w+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def jefferson_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Jefferson County, AL - Inmate Roster div-based layout."""
    url = "https://www.jeffcoso.org/roster.php"
    try:
        html = fetch_html(url)
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        # Find all inmate blocks - each starts with inmate_div
        blocks = re.findall(r'<div class="column medium-6 inmate_div">(.*?)(?=<div class="column medium-6 inmate_div"|<hr class="show-for-small-only">)', html, re.DOTALL | re.IGNORECASE)
        
        for block in blocks:
            # Extract name from <strong class="ptitles" style="float:left;">Last, First</strong>
            name_match = re.search(r'<strong class="ptitles"[^>]*>([^<]+)</strong>', block)
            if not name_match:
                continue
            
            name = name_match.group(1).strip()
            if not name or len(name) < 3:
                continue
            
            # Extract booking number
            booking_match = re.search(r'<span class="text2">(\d+)</span>', block)
            booking_num = booking_match.group(1) if booking_match else ""
            
            # Extract booking date
            date_match = re.search(r'<span class="text2">(\d{2}-\d{2}-\d{4}\s*-\s*\d{1,2}:\d{2}\s*(?:am|pm))</span>', block, re.IGNORECASE)
            booking_date = date_match.group(1) if date_match else ""
            
            # Extract charges - look for text after "Charges:"
            charges = []
            charges_match = re.search(r'Charges:\s*</strong>\s*</div>\s*<div[^>]*>(.*?)</div>', block, re.DOTALL | re.IGNORECASE)
            if charges_match:
                charges_text = charges_match.group(1)
                charges = [clean_html_text(c).strip() for c in re.split(r'<br\s*/?>|[\n\r]+', charges_text) if c.strip() and len(clean_html_text(c).strip()) > 3]
            
            first_name, last_name = split_name(name)
            charge_objs = [{"source_id": f"c{i+1}", "description": c, "statute": None, "severity": None}
                           for i, c in enumerate(charges)]
            if not charge_objs:
                charge_objs = [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}]
            
            records.append({
                "state": "AL", "county": "Jefferson", "facility": "Jefferson County Jail",
                "source_url": url, "source_type": "custom_html",
                "pulled_at": now, "booking_number": booking_num,
                "full_name": name, "first_name": first_name, "last_name": last_name,
                "booking_date": parse_iso(booking_date), "charges": charge_objs, "status": "in_custody",
            })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def mobile_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Mobile County, AL - roster loaded via iframe from all.mobileso.com."""
    url = "https://all.mobileso.com/OthReports/CurrentInmates.aspx"
    try:
        html = fetch_html(url)
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        # Find main roster table
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        
        for table in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
            if len(rows) < 2:
                continue
            
            for row in rows[1:]:  # skip header
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if len(cells) < 3:
                    continue
                
                cell_texts = [clean_html_text(c) for c in cells]
                name = cell_texts[0] if cell_texts else ""
                if not name or len(name) < 3 or name.lower() == "name":
                    continue
                
                booking_date = cell_texts[1] if len(cell_texts) > 1 else ""
                charges_text = cell_texts[2] if len(cell_texts) > 2 else ""
                
                first_name, last_name = split_name(name)
                charges = [{"source_id": f"c{i+1}", "description": c.strip(), "statute": None, "severity": None}
                           for i, c in enumerate(re.split(r"[<>;\n]+", charges_text)) if c.strip() and len(c.strip()) > 3]
                if not charges:
                    charges = [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}]
                
                records.append({
                    "state": "AL", "county": "Mobile", "facility": "Mobile County Jail",
                    "source_url": url, "source_type": "html_table",
                    "pulled_at": now, "full_name": name,
                    "first_name": first_name, "last_name": last_name,
                    "booking_date": parse_iso(booking_date), "charges": charges, "status": "in_custody",
                })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def madison_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Madison County, AL - SmartWEB roster."""
    url = "https://www.madisoncountysheriffal.org/inmate-roster"
    try:
        html = fetch_html(url)
        # SmartWEB — extract iframe or redirect
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html, re.IGNORECASE)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            if iframe_url.startswith("/"):
                iframe_url = f"https://www.madisoncountysheriffal.org{iframe_url}"
            html = fetch_html(iframe_url)
        
        # Parse SmartWEB table
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        # Look for booking entries in the rendered HTML
        blocks = re.split(r'<div[^>]*class="[^"]*(?:inmate|roster|booking)[^"]*"[^>]*>', html, flags=re.IGNORECASE)
        
        for block in blocks:
            text = clean_html_text(re.sub(r"<[^>]+>", " ", block))
            if len(text) < 50:
                continue
            
            # Extract name, booking number, etc.
            name_match = re.search(r"([A-Z][A-Z\s,]+)(?:\s*\(|\n)", text)
            booking_match = re.search(r"Booking\s*(?:#|Number)\s*:\s*([^\n]+)", text)
            date_match = re.search(r"Booking\s*(?:Date|Time)\s*:\s*(\d{1,2}/\d{1,2}/\d{4}[^\n]*)", text)
            desc_match = re.search(r"Description:\s*([^\n]+(?:\n(?!\s*(?:Booking|Gender|Race|Age|Bond|Status))[^\n]+)*)", text)
            
            if not name_match:
                continue
            
            name = name_match.group(1).strip()
            if len(name) < 3:
                continue
            
            first_name, last_name = split_name(name)
            charges = [{"source_id": "c1", "description": desc_match.group(1).strip(), "statute": None, "severity": None}] if desc_match else []
            
            records.append({
                "state": "AL", "county": "Madison", "facility": "Madison County Jail",
                "source_url": url, "source_type": "smartweb",
                "pulled_at": now, "booking_number": booking_match.group(1).strip() if booking_match else "",
                "full_name": name, "first_name": first_name, "last_name": last_name,
                "booking_date": parse_iso(date_match.group(1)) if date_match else None,
                "charges": charges, "status": "in_custody",
            })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def montgomery_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Montgomery County, AL."""
    url = "https://sheriff.montgomeryal.gov/"
    try:
        html = fetch_html(url)
        # Find iframe or redirect to actual roster
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html, re.IGNORECASE)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            html = fetch_html(iframe_url)
        
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        # Parse table if present
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if len(cells) < 3:
                    continue
                
                cell_texts = [clean_html_text(c) for c in cells]
                name = cell_texts[0]
                if not name or len(name) < 3:
                    continue
                
                first_name, last_name = split_name(name)
                records.append({
                    "state": "AL", "county": "Montgomery", "facility": "Montgomery County Jail",
                    "source_url": url, "source_type": "html_table",
                    "pulled_at": now, "full_name": name,
                    "first_name": first_name, "last_name": last_name,
                    "booking_date": parse_iso(cell_texts[1] if len(cell_texts) > 1 else ""),
                    "charges": [{"source_id": "c1", "description": cell_texts[2] if len(cell_texts) > 2 else "Unknown", "statute": None, "severity": None}],
                    "status": "in_custody",
                })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def baldwin_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Baldwin County, AL - search form."""
    url = "https://sheriff.baldwincountyal.gov/home/arrest-search"
    try:
        html = fetch_html(url)
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        # Look for roster data in tables or divs
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if len(cells) < 2:
                    continue
                
                cell_texts = [clean_html_text(c) for c in cells]
                name = cell_texts[0]
                if not name or len(name) < 3:
                    continue
                
                first_name, last_name = split_name(name)
                records.append({
                    "state": "AL", "county": "Baldwin", "facility": "Baldwin County Jail",
                    "source_url": url, "source_type": "html_table",
                    "pulled_at": now, "full_name": name,
                    "first_name": first_name, "last_name": last_name,
                    "booking_date": parse_iso(cell_texts[1] if len(cell_texts) > 1 else ""),
                    "charges": [{"source_id": "c1", "description": "Unknown", "statute": None, "severity": None}],
                    "status": "in_custody",
                })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def elmore_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Elmore County, AL - uses roster.frameset."""
    url = "https://www.elmoreso.com/inmate-roster/"
    try:
        html = fetch_html(url)
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        # Parse table if present
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if len(cells) < 3:
                    continue
                
                cell_texts = [clean_html_text(c) for c in cells]
                name = cell_texts[0]
                if not name or len(name) < 3:
                    continue
                
                first_name, last_name = split_name(name)
                records.append({
                    "state": "AL", "county": "Elmore", "facility": "Elmore County Jail",
                    "source_url": url, "source_type": "html_table",
                    "pulled_at": now, "full_name": name,
                    "first_name": first_name, "last_name": last_name,
                    "booking_date": parse_iso(cell_texts[1] if len(cell_texts) > 1 else ""),
                    "charges": [{"source_id": "c1", "description": cell_texts[2] if len(cell_texts) > 2 else "Unknown", "statute": None, "severity": None}],
                    "status": "in_custody",
                })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def houston_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Houston County, AL."""
    url = "https://www.hcsheriff.org/inmate-roster/"
    try:
        html = fetch_html(url)
        records = []
        now = datetime.now(timezone.utc).isoformat()
        
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        for table in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
            for row in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if len(cells) < 3:
                    continue
                
                cell_texts = [clean_html_text(c) for c in cells]
                name = cell_texts[0]
                if not name or len(name) < 3:
                    continue
                
                first_name, last_name = split_name(name)
                records.append({
                    "state": "AL", "county": "Houston", "facility": "Houston County Jail",
                    "source_url": url, "source_type": "html_table",
                    "pulled_at": now, "full_name": name,
                    "first_name": first_name, "last_name": last_name,
                    "booking_date": parse_iso(cell_texts[1] if len(cell_texts) > 1 else ""),
                    "charges": [{"source_id": "c1", "description": cell_texts[2] if len(cell_texts) > 2 else "Unknown", "statute": None, "severity": None}],
                    "status": "in_custody",
                })
        
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


# Registry of all Alabama adapters
ALABAMA_ADAPTERS = {
    "jefferson_county_al": jefferson_county_al,   # 19 records - roster.php div layout
    "mobile_county_al": mobile_county_al,         # 1669 records - iframe from all.mobileso.com
    "madison_county_al": madison_county_al,       # SmartWEB portal
    "montgomery_county_al": montgomery_county_al, # NewWorld portal
    "tuscaloosa_county_al": mobile_county_al,     # Same iframe pattern as Mobile
    "baldwin_county_al": baldwin_county_al,       # Search form
    "elmore_county_al": elmore_county_al,         # Roster page
    "houston_county_al": houston_county_al,       # Roster page
}

# County name to adapter mapping
COUNTY_ADAPTER_MAP = {
    "Jefferson": "jefferson_county_al",
    "Mobile": "mobile_county_al",
    "Madison": "madison_county_al",
    "Montgomery": "montgomery_county_al",
    "Tuscaloosa": "tuscaloosa_county_al",
    "Baldwin": "baldwin_county_al",
    "Elmore": "elmore_county_al",
    "Houston": "houston_county_al",
    "Lee": "mobile_county_al",  # Same system
    "Shelby": "jefferson_county_al",  # Same system
}
