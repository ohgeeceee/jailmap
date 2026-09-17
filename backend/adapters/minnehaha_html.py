from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List

from backend.adapters.idaho import AdapterResult, _fetch_html, _now_iso, _parse_iso

URL = "https://web.minnehahacounty.gov/dept/so/jailInmateInfo/browseJailInmate.php"


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _to_float(value: str):
    value = value.replace("$", "").replace(",", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else None


def _split_name(value: str):
    parts = value.split()
    return parts[0] if parts else "", " ".join(parts[1:]) if len(parts) > 1 else ""


def fetch(source) -> List[Dict]:
    html = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    tbody = html[html.lower().find("<tbody>"):html.lower().find("</tbody>")]
    rows: List[Dict] = []
    for block in re.findall(r"<tr>(.*?)</tr>", tbody, re.S):
        cells = re.findall(r"<td>(.*?)</td>", block, re.S)
        if len(cells) != 9:
            continue
        first = _clean(cells[0])
        middle = _clean(cells[1])
        last = _clean(re.sub(r"\d+$", "", cells[2]))
        file_id = re.search(r"(\d{4,})", cells[2])
        booking_number = file_id.group(1) if file_id else f"{first}-{last}-{_clean(cells[4])}"
        intake_date = _parse_iso(_clean(cells[4]))
        intake_time = _clean(cells[5])
        booking_date = intake_date
        if intake_date and intake_time:
            combined = f"{intake_date} {intake_time}"
            parsed = _parse_iso(combined)
            if parsed:
                booking_date = parsed
        facility = _clean(cells[6])
        bond = _to_float(_clean(cells[7]))
        charges_text = _clean(re.sub(r"<br\s*/?>", " | ", cells[8], flags=re.I))
        charges = [{"source_id": "c1", "description": charges_text, "statute": None, "severity": None}] if charges_text else []
        bonds = [{"source_id": "b1", "amount": bond, "type": "bond", "status": "set" if bond is not None else "unknown"}]
        first_name, last_name = _split_name(f"{first} {middle} {last}".strip())
        rows.append({
            "state": "SD",
            "county": source["county"],
            "facility": facility or source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "custom_html",
            "pulled_at": _now_iso(),
            "booking_number": booking_number,
            "full_name": " ".join(x for x in [first_name, middle, last_name] if x),
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": None,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "release_date": None,
            "charges": charges,
            "bonds": bonds,
            "status": "in_custody",
            "mugshot_url": None,
            "custody_level": None,
            "source_updated_at": _now_iso(),
            "visibility": "public",
        })
    return rows
