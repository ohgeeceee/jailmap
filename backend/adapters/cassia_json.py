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
    """Parse Cassia County JSON inmate roster API."""
    # The data URL is derived from the page URL
    base_url = source.get("source_url", "").rstrip("/")
    if "/jail-roster" in base_url:
        data_url = base_url.replace("/jail-roster", "/jail-roster-data/roster/")
    else:
        data_url = base_url
    
    text = _fetch_html(data_url).decode("utf-8", errors="ignore")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    import json
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return AdapterResult(source, [])
    
    rows = data.get("rows", [])
    for row in rows:
        name = row.get("name", "")
        # Parse name: "LAST, FIRST MIDDLE" or "LAST, #### ####" (redacted)
        if "," in name:
            parts = name.split(",", 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # Parse charges
        charges = []
        for i, charge in enumerate(row.get("charges", [])):
            charges.append({
                "source_id": f"c{i+1}",
                "description": charge.get("case_number", ""),
                "statute": None,
                "severity": None,
            })
        
        # Parse booking date
        booking_date = row.get("booked", "")
        
        # Parse bond amount
        bond_amount = None
        for charge in row.get("charges", []):
            bond = charge.get("bond_amount", 0)
            if bond and bond > 0:
                bond_amount = float(bond)
                break
        
        records.append({
            "state": "ID",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": data_url,
            "source_type": "json",
            "source_updated_at": pulled_at,
            "inmate_id": row.get("booking_id", "").split()[0] if " " in row.get("booking_id", "") else row.get("booking_id", ""),
            "booking_number": row.get("booking_id", "").split()[0] if " " in row.get("booking_id", "") else row.get("booking_id", ""),
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": row.get("age"),
            "sex": row.get("sex"),
            "race": row.get("race"),
            "booking_date": booking_date,
            "release_date": None,
            "charges": charges or [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}],
            "bond_amount": bond_amount,
            "status": "in_custody", "visibility": "public",
            "mugshot_url": row.get("photo_url"),
            "notes": f"Type: {row.get('inmate_type', '')}, Days: {row.get('days_in_jail', '')}",
        })
    
    return AdapterResult(source, records)
