from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _to_float(value: Optional[str]) -> Optional[float]:
    value = _clean_text(value)
    if not value:
        return None
    value = value.replace("$", "").replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    if not match:
        return None
    return float(match.group(0))


def _extract_updated(text: str) -> Optional[str]:
    match = re.search(r"Updated\s+(?P<ts>[A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[A-Z]{3,5})", text)
    if not match:
        return None
    return match.group("ts")


def parse(source) -> AdapterResult:
    text = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    updated = _extract_updated(text)
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    for block in re.findall(r"<tr>(.*?)</tr>", text, re.DOTALL | re.IGNORECASE):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", block, re.DOTALL | re.IGNORECASE)
        if len(cells) < 5:
            continue
        mug_match = re.search(r'(?:href|src)="(?P<mug>https?://[^"]+)"', cells[0], re.IGNORECASE)
        if not mug_match:
            continue
        inmate_id, last_name, first_name, location = cells[1:5]
        if not _clean_text(inmate_id).isdigit():
            continue
        import hashlib
        _bn_src = (mug_match.group("mug") if mug_match else "") or (inmate_id or full_name)
        booking_number = "BNV-" + hashlib.sha1(_bn_src.encode()).hexdigest()[:10]
        records.append({
            "state": "ID",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "inmate_id": _clean_text(inmate_id),
            "booking_number": booking_number,
            "full_name": f"{_clean_text(first_name).strip()} {_clean_text(last_name).strip()}".strip(),
            "first_name": _clean_text(first_name).strip(),
            "last_name": _clean_text(last_name).strip(),
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": updated or pulled_at,
            "release_date": None,
            "charges": [],
            "bonds": [],
            "bond_amount": None,
            "status": "in_custody",
            "mugshot_url": mug_match.group("mug").strip(),
            "source_updated_at": pulled_at,
            "visibility": "public",
            "notes": _clean_text(location),
        })

    return AdapterResult(source, records)
