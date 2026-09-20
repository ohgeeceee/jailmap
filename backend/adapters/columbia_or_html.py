from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def parse(source) -> AdapterResult:
    """Parse Columbia County HTML inmate roster."""
    text = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    # Parse table rows
    rows = re.findall(r'<tr>(.*?)</tr>', text, re.DOTALL | re.IGNORECASE)
    
    for row in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
        clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        
        # Skip header rows and empty rows
        if len(clean_cells) < 6:
            continue
        
        # Skip rows where first cell is not a number
        if not clean_cells[0].isdigit():
            continue
        
        # Parse row: #, Name, Book Date, Charge, Bail, Release Date
        try:
            num = clean_cells[0]
            name = clean_cells[1]
            book_date = clean_cells[2]
            charge = clean_cells[3]
            bail = clean_cells[4]
            release_date = clean_cells[5] if len(clean_cells) > 5 else ''
        except IndexError:
            continue
        
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
        
        # Parse bail amount
        bond_amount = None
        if bail and bail != '$0.00':
            try:
                bond_amount = float(bail.replace('$', '').replace(',', ''))
            except ValueError:
                pass
        
        records.append({
            "state": "OR",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "source_updated_at": pulled_at,
            "inmate_id": num,
            "booking_number": num,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": book_date,
            "release_date": release_date if release_date else None,
            "charges": [{"source_id": "c1", "description": charge, "statute": None, "severity": None}] if charge else [],
            "bond_amount": bond_amount,
            "status": "in_custody", "visibility": "public",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
