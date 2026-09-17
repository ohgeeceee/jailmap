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


def _parse_mug_and_name(block: str):
    md = re.search(r"!\[\]\((?P<mug>[^)]+)\)\s*\*\*(?P<name>[^*]+)\*\*", block)
    if md:
        return md.group("mug").strip(), _clean_text(md.group("name"))
    html_img = re.search(r"<img[^>]+src=[\"'](?P<mug>[^\"']+)[\"'][^>]*>", block)
    if html_img:
        mugshot_url = html_img.group("mug").strip()
        alt_match = re.search(r"alt=[\"']Mugshot of\s+(?P<name>[^\"']+)[\"']", block)
        html_name = _clean_text(alt_match.group("name")) if alt_match else ""
        if not html_name:
            bold = re.search(r"\*\*(?P<name>[^*]+)\*\*", block)
            html_name = _clean_text(bold.group("name")) if bold else ""
        return mugshot_url, html_name
    return None, ""


def parse(source) -> AdapterResult:
    text = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    for block in re.split(r"\* \* \*", text):
        mugshot_url, full_name = _parse_mug_and_name(block)
        if not full_name:
            continue
        full_name = _clean_text(full_name)
        full_name = re.sub(r"^\*\*|\*\*$", "", full_name)
        if "," in full_name:
            last_name, first_name = full_name.split(",", 1)
            full_name = f"{first_name.strip()} {last_name.strip()}"
        booking_number = None
        booking_date = None
        bond_amount = None
        charges: List[str] = []
        booking_match = re.search(r"\*\*Booking #:\*\*\s*\n?\s*(?P<value>[^\n]+)", block)
        if booking_match:
            booking_number = _clean_text(booking_match.group("value"))
        date_match = re.search(r"\*\*Booking Date:\*\*\s*\n?\s*(?P<value>[^\n]+)", block)
        if date_match:
            booking_date = _parse_iso(_clean_text(date_match.group("value")))
        bond_match = re.search(r"\*\*Bond:\*\*\s*\n?\s*(?P<value>[^\n]+)", block)
        if bond_match:
            bond_amount = _to_float(bond_match.group("value"))
        charge_section = re.search(r"\*\*Charges:\*\*\s*\n?\s*(?P<value>.*?)(?:\n\s*_\*\*View Profile|$)", block, re.S)
        if charge_section:
            charges = [_clean_text(line) for line in charge_section.group("value").splitlines() if _clean_text(line)]
        first_name = full_name.split(" ", 1)[0] if full_name else ""
        last_name = full_name.split(" ", 1)[1] if full_name and " " in full_name else ""
        records.append({
            "state": "ID",
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": pulled_at,
            "booking_number": booking_number,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "release_date": None,
            "charges": charges or ["Unknown charge"],
            "bond_amount": bond_amount,
            "status": "in_custody",
            "mugshot_url": mugshot_url,
            "notes": source.get("adapter_strategy"),
        })

    return AdapterResult(source, records)
