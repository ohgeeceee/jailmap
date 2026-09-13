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


def parse(source) -> AdapterResult:
    text = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    # Live page uses relative hrefs (BookingInfo.aspx?id=N); accept an optional
    # /jailroster/ prefix so both forms match.
    for inmate_link in re.findall(r"<a[^>]+href=\"(?P<url>(?:/jailroster/)?BookingInfo\.aspx\?id=\d+)\"[^>]*>(?P<name>[^<]+)</a>", text):
        url, name = inmate_link
        booking_number = f"PWR-{url.split('id=')[-1]}"
        full_name = _clean_text(name)
        full_name = re.sub(r"^\*\*|\*\*$", "", full_name)
        if "," in full_name:
            last_name, first_name = full_name.split(",", 1)
            full_name = f"{first_name.strip()} {last_name.strip()}"
        first_name = full_name.split(" ", 1)[0]
        last_name = full_name.split(" ", 1)[1] if " " in full_name else ""
        records.append({
            "state": "ID",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "inmate_id": None,
            "booking_number": booking_number,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": pulled_at,
            "release_date": None,
            "charges": [],
            "bonds": [],
            "bond_amount": None,
            "status": "in_custody",
            "mugshot_url": None,
            "source_updated_at": pulled_at,
            "visibility": "public",
            "notes": url,
        })

    return AdapterResult(source, records)
