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
    """Parse Washington County HTML inmate roster."""
    text = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    # Pattern: NAME</A> TIME DATE ID <a href="...">
    # Example: >VICHI TAPIA, SERGIO         </A> 14:29:02 07/28/26
    #    841929 <a href="...">
    pattern = r'>([A-Z][A-Z\s,\-/]+)\s*</A>\s+(\d{2}:\d{2}:\d{2}\s+\d{2}/\d{2}/\d{2})\s*\n?\s*(\d{6})\s*<a'
    
    for match in re.finditer(pattern, text):
        name = match.group(1).strip()
        booking_date = match.group(2).strip()
        inmate_id = match.group(3).strip()
        
        # Parse name: "LASTNAME, FIRST MIDDLE"
        if "," in name:
            parts = name.split(",", 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            parts = name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        records.append({
            "state": "ID",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "inmate_id": inmate_id,
            "booking_number": None,
            "full_name": f"{first_name} {last_name}".strip(),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "release_date": None,
            "charges": [],
            "bond_amount": None,
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
