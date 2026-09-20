from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

STATUS_MAP = {
    "in jail": "in_custody",
    "released": "released",
}
SOURCE_TIMEZONES = {"FL": ZoneInfo("America/New_York")}

BOOKNO_RE = re.compile(r"bookno=([A-Z0-9]+)")
IMG_RE = re.compile(r"<img[^>]*bookno=[A-Z0-9]+[^>]*>", re.IGNORECASE)
NAME_RE = re.compile(r'<td class="SearchHeader"[^>]*>\s*([^<]+?)\s*(?:\&nbsp;)?\s*\(', re.IGNORECASE)
BOOKING_DATE_RE = re.compile(r"Booking Date:\s*([0-9/]+\s+[0-9:]+\s*(?:AM|PM)?)", re.IGNORECASE)
MNI_NO_RE = re.compile(r"MniNo:\s*([A-Z0-9]+)")
AGE_RE = re.compile(r"Age On Booking Date:\s*(\d+)")
BOND_RE = re.compile(r"Bond Amount:\s*\$?([0-9,.]+|NO BOND)")
STATUS_RE = re.compile(r"Status:\s*(In Jail|Released)", re.IGNORECASE)
CHARGE_RE = re.compile(
    r"<td[^>]*>\s*(?:\[\+?\]\s*)?</td>\s*"
    r"<td[^>]*>([^<]*)</td>\s*"
    r"<td[^>]*>([^<]*)</td>\s*"
    r"<td[^>]*>([^<]*)</td>\s*"
    r"<td[^>]*>([^<]*)</td>\s*"
    r"<td[^>]*>([^<]*)</td>\s*"
    r"<td[^>]*>\$?([0-9,.]+)</td>",
    re.IGNORECASE,
)


def _parse_date(value: str, state: str = "FL") -> str:
    if not value or not value.strip():
        return ""
    value = value.strip()
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            source_timezone = SOURCE_TIMEZONES.get(state)
            if source_timezone is None:
                raise ValueError(f"SmartWEB timezone is not configured for {state}")
            return dt.replace(tzinfo=source_timezone).isoformat()
        except ValueError:
            continue
    return value


def _status(value: str) -> Optional[str]:
    return STATUS_MAP.get(value.strip().lower())


def _name_parts(raw: str) -> tuple:
    name = (raw or "").strip()
    if not name:
        return "", ""
    if "," in name:
        last, first = name.split(",", 1)
        return first.strip().title(), last.strip().title()
    parts = name.split()
    if len(parts) >= 2:
        return parts[0].title(), " ".join(parts[1:]).title()
    return name.title(), ""


def fetch(source) -> AdapterResult:
    _assert_authorized(source["source_url"])
    with httpx.Client(timeout=45, follow_redirects=True) as client:
        resp = client.get(source["source_url"], headers=HEADERS)
        resp.raise_for_status()
        html = resp.text

    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    seen_bookings = set()

    # Split on image tags that contain bookno
    blocks = IMG_RE.split(html)
    blocks = blocks[1:]  # skip header before first image

    for block in blocks:
        block_text = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", block))).strip()
        bookno_match = BOOKNO_RE.search(block)
        if not bookno_match:
            continue

        booking_number = bookno_match.group(1)
        if booking_number in seen_bookings:
            raise ValueError("Duplicate booking number in complete SmartWEB snapshot")
        seen_bookings.add(booking_number)

        # Name from SearchHeader td
        name_match = NAME_RE.search(block)
        name_raw = name_match.group(1) if name_match else ""
        first_name, last_name = _name_parts(name_raw)

        # Booking date
        date_match = BOOKING_DATE_RE.search(block_text)
        booking_date = _parse_date(date_match.group(1), str(source.get("state", "FL"))) if date_match else ""
        if not booking_date:
            raise ValueError("SmartWEB row is missing a valid booking date")

        # MNI number
        mni_match = MNI_NO_RE.search(block_text)
        mni_no = mni_match.group(1) if mni_match else ""

        # Age
        age_match = AGE_RE.search(block_text)
        if not age_match:
            raise ValueError("SmartWEB row is missing a parseable adult-eligibility age")
        age = int(age_match.group(1))
        if age < 18:
            continue

        # Status
        status_match = STATUS_RE.search(block_text)
        status = _status(status_match.group(1)) if status_match else None
        if status not in {"in_custody", "released"}:
            raise ValueError("SmartWEB row has an unknown custody status")

        # Bond
        bond_match = BOND_RE.search(block_text)
        bond_text = bond_match.group(1) if bond_match else ""
        bond_amount = None
        if bond_text and bond_text.upper() != "NO BOND":
            try:
                bond_amount = float(bond_text.replace(",", ""))
            except ValueError:
                bond_amount = None

        # Charges
        charges = []
        for cm in CHARGE_RE.finditer(block):
            statute = cm.group(1).strip()
            case_number = cm.group(2).strip()
            charge_desc = cm.group(3).strip()
            degree = cm.group(4).strip()
            level = cm.group(5).strip()
            charge_bond = cm.group(6).strip()
            if not statute and not charge_desc:
                continue
            charge_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{booking_number}|{statute}|{case_number}|{charge_desc}",
            ))[:12]
            charges.append({
                "source_id": charge_id,
                "description": charge_desc[:2000] if charge_desc else statute[:2000],
                "statute": statute or None,
                "severity": degree or level or None,
            })

        identity = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{booking_number}|{mni_no}|{name_raw}|{booking_date}",
        ))[:16]

        records.append({
            "state": source.get("state", "FL"),
            "county": source["county"],
            "facility": source["facility_name"],
            "source_url": source["source_url"],
            "source_type": "smartweb_portal",
            "pulled_at": pulled_at,
            "id": identity,
            "booking_number": booking_number,
            "mni_no": mni_no,
            "source_updated_at": booking_date,
            "full_name": name_raw,
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "release_date": None,
            "charges": charges,
            "bonds": [{"source_id": "b1", "amount": bond_amount, "type": "bond", "status": "set" if bond_amount is not None else "unknown"}] if bond_amount is not None else [],
            "status": status,
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
