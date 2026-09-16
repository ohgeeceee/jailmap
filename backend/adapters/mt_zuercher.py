"""Zuercher portal vendor adapter (MT counties).

One JSON POST API covers: ravalli, gallatin, jefferson, carbon, stillwater,
meagher, wheatland, roosevelt, madison (portal URL is the county's
zuercherportal.com subdomain, source_url ends in /#/inmates).
Reference: /root/montanablotter/services/ingestion/jail_bookings.py:998
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
    "Accept": "application/json,text/plain,*/*",
}
_TAG_RE = re.compile(r"<br\s*/?>|</?[a-z][^>]*>", re.IGNORECASE)


def _api_base(source_url: str) -> str:
    base = source_url.rstrip("/")
    if base.endswith("#/inmates"):
        base = base[:-9].rstrip("/")
    return base


def _holds_to_charges(hold_reasons: str) -> List[Dict]:
    """Split the <br />-separated hold_reasons blob into charge entries."""
    charges: List[Dict] = []
    seen_charges = set()
    for chunk in _TAG_RE.sub("\n", hold_reasons or "").split("\n"):
        chunk = unescape(chunk).strip()
        if not chunk:
            continue
        charge_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk))[:8]
        if charge_id in seen_charges:
            continue
        seen_charges.add(charge_id)
        charges.append({
            "id": charge_id,
            "description": chunk[:2000],
            "statute": None,
            "severity": None,
        })
    return charges


def _bonds_from_holds(hold_reasons: str) -> List[Dict]:
    bonds: List[Dict] = []
    seen_bonds = set()
    for match in re.finditer(r"Bond\s*-\s*([^,;]+),\s*\$?([\d,]+(?:\.\d{2})?)", hold_reasons or ""):
        bond_type, amount = match.group(1).strip(), match.group(2).replace(",", "")
        bond_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{bond_type}|{amount}"))[:8]
        if bond_id in seen_bonds:
            continue
        seen_bonds.add(bond_id)
        bonds.append({
            "source_id": bond_id,
            "amount": float(amount),
            "type": bond_type[:100] or "bond",
            "status": "set",
        })
    return bonds


def _name_parts(raw: str) -> tuple:
    name = (raw or "").strip()
    if "," in name:
        last, first = name.split(",", 1)
        return first.strip().title(), last.strip().title()
    parts = name.split()
    return (parts[1].title() if len(parts) > 1 else "", parts[0].title()) if parts else ("", "")


def fetch(source) -> AdapterResult:
    _assert_authorized(source["source_url"])
    base = _api_base(source["source_url"])
    headers = dict(_HEADERS)
    headers["Referer"] = f"{base}/#/inmates"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00.000Z")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    seen_ids = set()
    offset, page_size = 0, 50
    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        while True:
            response = client.post(
                f"{base}/api/portal/inmates/load",
                json={
                    "name": "", "race": "all", "sex": "all", "cell_block": "all",
                    "held_for_agency": "any", "in_custody": today,
                    "paging": {"start": offset, "count": page_size},
                    "sorting": {"sort_by_column_tag": "name", "sort_descending": False},
                },
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json() or {}
            rows = payload.get("records") or []
            for row in rows:
                first, last = _name_parts(row.get("name", ""))
                holds = row.get("hold_reasons", "") or ""
                # Stable identity: staging_key checks source_id first; the
                # name+date fallback collides on shared arrest dates.
                row_identity = "|".join([
                    (row.get("name") or ""), (row.get("arrest_date") or ""),
                    (row.get("held_for_agency") or ""), holds,
                ])
                identity = str(uuid.uuid5(uuid.NAMESPACE_URL, row_identity))[:16]
                if identity in seen_ids:
                    # Zuercher occasionally serves the same row twice
                    # (pagination boundary); keep one copy.
                    continue
                seen_ids.add(identity)
                # Public contract: booking_number and ISO timestamps required.
                booking_number = row.get("booking_number") or row.get("booking") or f"ZCR-{identity}"
                booking_date = None
                if (row.get("arrest_date") or "").strip():
                    booking_date = f"{row['arrest_date'].strip()}T12:00:00Z"
                if not booking_date:
                    booking_date = pulled_at.split(".")[0] + "Z" if "." in pulled_at else pulled_at
                records.append({
                    "state": "MT",
                    "county": source["county"],
                    "facility": source["facility_name"],
                    "source_url": source["source_url"],
                    "source_type": "zuercher_portal",
                    "pulled_at": pulled_at,
                    "id": identity,
                    "booking_number": booking_number,
                    "updated_at": booking_date or pulled_at,
                    "visibility": "public",
                    "full_name": (row.get("name") or "").strip(),
                    "first_name": first,
                    "last_name": last,
                    "dob": row.get("dob") or None,
                    "age": None,
                    "sex": row.get("sex") or None,
                    "race": row.get("race") or None,
                    "booking_date": booking_date,
                    "release_date": None,
                    "charges": _holds_to_charges(holds),
                    "bond_amount": None,
                    "bonds": _bonds_from_holds(holds),
                    "status": "in_custody",
                    "mugshot_url": row.get("mugshot") or None,
                    "notes": None,
                })
            if len(rows) < page_size or len(records) > 5000:
                break
            offset += page_size
    return AdapterResult(source, records)
