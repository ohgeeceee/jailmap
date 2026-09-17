from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _to_int(value: Optional[str]) -> Optional[int]:
    value = _clean_text(value)
    if not value:
        return None
    match = re.search(r"\d+", value.replace(",", ""))
    if not match:
        return None
    return int(match.group(0))


def parse(source) -> AdapterResult:
    content = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    records: List[Dict] = []
    blocks = re.split(r"\n\s*\n", content)
    for block in blocks:
        if "Booking #:" not in block and "Booking Date:" not in block:
            continue
        name_match = re.search(r"\*\*(?P<name>[^\*]+)\*\*", block)
        booking_match = re.search(r"\*\*Booking #:\*\*\s*\n?\s*(?P<number>[^\n]+)", block)
        date_match = re.search(r"\*\*Booking Date:\*\*\s*\n?\s*(?P<date>[^\n]+)", block)
        if not name_match:
            continue
        full_name = _clean_text(name_match.group("name"))
        first_name = full_name.split(" ", 1)[0] if full_name else ""
        last_name = full_name.split(" ", 1)[1] if full_name and " " in full_name else ""
        charges: List[str] = []
        for charge_line in re.findall(r"\n\s*-\s*([^\n_]+)", block):
            charge_line = _clean_text(charge_line)
            if charge_line and charge_line not in {"View Profile >>>"}:
                charges.append(charge_line)
        records.append({
            "state": "ID",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": datetime.now(timezone.utc).isoformat(),
            "booking_number": _clean_text(booking_match.group("number")) if booking_match else None,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": _parse_iso(_clean_text(date_match.group("date"))) if date_match else None,
            "release_date": None,
            "scheduled_release": None,
            "charges": [{"source_id": f"c{i+1}", "description": charge, "statute": None, "severity": None} for i, charge in enumerate(charges[:50])] or [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}],
            "status": "in_custody" if "released=1" not in source.get("source_url", "") else "released",
            "mugshot_url": None,
            "custody_level": None,
        })
    if not records:
        return AdapterResult(source, [])
    return AdapterResult(source, records)
