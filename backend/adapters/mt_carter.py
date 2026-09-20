"""Carter County Sheriff's Office — JSON API adapter.

Source: https://cartercountysheriff.us/inmate-search
API: https://cartercountysheriff.us/dmxConnect/api/Booking/Read.php
142 records, full data: name, DOB, booking date, charges, mugshot, address.
Pagination via offset/limit query params.
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlsplit

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
    "Accept": "application/json,text/plain,*/*",
}


def _name_parts(raw: str) -> tuple:
    name = (raw or "").strip()
    if "," in name:
        last, first = name.split(",", 1)
        return first.strip().title(), last.strip().title()
    parts = name.split()
    if len(parts) >= 2:
        return parts[0].title(), parts[-1].title()
    return (parts[0].title() if parts else "", "")


def _charges_from_blob(charges_str: str) -> List[Dict]:
    """Parse Carter's bullet-separated charge string."""
    charges: List[Dict] = []
    seen = set()
    for chunk in re.split(r"<br\s*/?>|•|;", charges_str or ""):
        chunk = chunk.strip().strip("•").strip()
        if not chunk:
            continue
        cid = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk))[:8]
        if cid in seen:
            continue
        seen.add(cid)
        charges.append({
            "source_id": cid,
            "description": chunk[:2000],
            "statute": None,
            "severity": None,
        })
    return charges


def _parse_iso(raw: str) -> str:
    if not raw or not raw.strip():
        return ""
    raw = raw.strip()
    try:
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        pass
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        pass
    return raw


def fetch(source) -> AdapterResult:
    _assert_authorized(source["source_url"])
    pulled_at = datetime.now(timezone.utc).isoformat()
    base = source["source_url"].rstrip("/")
    # source_url is the roster page URL; API is at the site root
    if "/inmate-search" in base:
        api_base = base.replace("/inmate-search", "")
    else:
        api_base = base
    roster_url = f"{api_base.rstrip('/')}/dmxConnect/api/Booking/Read.php"

    records: List[Dict] = []
    seen_ids = set()
    offset, page_size = 0, 25

    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        while True:
            resp = client.get(
                roster_url,
                params={"offset": offset, "limit": page_size},
                headers=_HEADERS,
            )
            resp.raise_for_status()
            payload = resp.json() or {}
            query = payload.get("querybookings") or {}
            data = query.get("data") or []
            total = query.get("total", 0)

            for row in data:
                booking_num = row.get("BookingNum") or row.get("BookingID")
                identity = str(uuid.uuid5(uuid.NAMESPACE_URL, booking_num or row.get("InmateID", "")))[:16]
                if identity in seen_ids:
                    continue
                seen_ids.add(identity)

                first, last = _name_parts(row.get("FullName", ""))
                booking_date = _parse_iso(row.get("BookingDate", ""))
                mugshot_file = row.get("Pic", "") or ""
                mugshot_url = f"{base}/app/showmugshot/{mugshot_file}" if mugshot_file else None
                charges = _charges_from_blob(row.get("Charges", ""))

                records.append({
                    "state": "MT",
                    "county": "Carter",
                    "facility": "Carter County Justice Center",
                    "source_url": source["source_url"],
                    "source_type": "json_api",
                    "pulled_at": pulled_at,
                    "id": identity,
                    "booking_number": booking_num,
                    "source_updated_at": booking_date or pulled_at,
                    "visibility": "public",
                    "full_name": row.get("FullName", "").strip(),
                    "first_name": first or row.get("FName", "").strip().title(),
                    "last_name": last or row.get("LName", "").strip().title(),
                    "dob": row.get("dob") or None,
                    "sex": row.get("Sex") or None,
                    "race": row.get("Race") or None,
                    "booking_date": booking_date or pulled_at,
                    "release_date": _parse_iso(row.get("ReleaseDate", "")) or None,
                    "charges": charges,
                    "bond_amount": None,
                    "bonds": [],
                    "status": "in_custody",
                    "mugshot_url": mugshot_url,
                    "notes": row.get("heldfor") or None,
                })

            if len(data) < page_size or len(records) >= total or len(records) > 5000:
                break
            offset += page_size

    return AdapterResult(source, records)
