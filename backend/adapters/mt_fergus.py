"""Fergus County, Montana — HTML accordion roster adapter.

Source: https://fergusmt.gov/detention-center-roster
Structure: Bootstrap accordion with inmate names as headers, booking details
in collapsible panels. Each panel contains booking date, charges, bond, court info.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
    "Accept": "text/html,application/xhtml+xml",
}

_BOOKED_RE = re.compile(r"Booked in on:\s*(\d{1,2}/\d{1,2}/\d{4})")
_CHARGES_RE = re.compile(r"(?:Original Charges|Charges):\s*([^\n<]+)")
_WARRANT_RE = re.compile(r"Warrant:\s*\(([^)]+)\)\s*([^\n<]+)")
_BOND_RE = re.compile(r"Bond\s*\$([\d,]+)")
_HOLD_RE = re.compile(r"(Courtesy Hold|ICE Detainer|DOC Hold|No Bond)")


def _parse_date(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.strptime(raw.strip(), "%m/%d/%Y")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        pass
    return raw


def fetch(source) -> AdapterResult:
    _assert_authorized(source["source_url"])
    pulled_at = datetime.now(timezone.utc).isoformat()

    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        resp = client.get(source["source_url"], headers=_HEADERS)
        resp.raise_for_status()
        html = resp.text

    records: List[Dict] = []
    seen_ids = set()

    # Each inmate is an accordion panel
    panels = re.findall(
        r'<span[^>]*class="[^"]*sppb-panel-title[^"]*"[^>]*aria-label="([^"]+)"[^>]*>(.*?)</span>.*?'
        r'<div[^>]*class="[^"]*sppb-panel-body[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html, re.DOTALL
    )

    for name_raw, span_content, body in panels:
        name = unescape(name_raw).strip()
        # Skip non-inmate panels (like navigation headers)
        if not any(c.isalpha() for c in name) or "Navigation" in name or "Search" in name or len(name) < 4:
            continue
        body_text = unescape(re.sub(r"<[^>]+>", " ", body)).strip()
        body_text = re.sub(r"\s+", " ", body_text)

        # Extract booking date
        booking_match = _BOOKED_RE.search(body_text)
        booking_date = _parse_date(booking_match.group(1)) if booking_match else ""

        # Extract charges
        charges: List[Dict] = []
        seen_charges = set()
        for m in _CHARGES_RE.finditer(body_text):
            desc = m.group(1).strip().strip("()")
            cid = str(uuid.uuid5(uuid.NAMESPACE_URL, desc))[:8]
            if cid not in seen_charges:
                seen_charges.add(cid)
                charges.append({"source_id": cid, "description": desc, "statute": None, "severity": None})
        for m in _WARRANT_RE.finditer(body_text):
            desc = f"({m.group(1)}) {m.group(2).strip()}"
            cid = str(uuid.uuid5(uuid.NAMESPACE_URL, desc))[:8]
            if cid not in seen_charges:
                seen_charges.add(cid)
                charges.append({"source_id": cid, "description": desc, "statute": None, "severity": None})

        # Extract bond
        bonds: List[Dict] = []
        seen_bonds = set()
        for m in _BOND_RE.finditer(body_text):
            amount = m.group(1).replace(",", "")
            bid = str(uuid.uuid5(uuid.NAMESPACE_URL, amount))[:8]
            if bid not in seen_bonds:
                seen_bonds.add(bid)
                bonds.append({"source_id": bid, "amount": float(amount), "type": "bond", "status": "set"})

        # Name parsing
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0].title()
            last_name = " ".join(name_parts[1:]).title()
        else:
            first_name = name
            last_name = ""

        identity = str(uuid.uuid5(uuid.NAMESPACE_URL, name))[:16]
        if identity in seen_ids:
            continue
        seen_ids.add(identity)

        hold_match = _HOLD_RE.search(body_text)
        status_note = hold_match.group(1) if hold_match else None

        records.append({
            "state": "MT",
            "county": "Fergus",
            "facility": "Fergus County Detention Center",
            "source_url": source["source_url"],
            "source_type": "html_roster",
            "pulled_at": pulled_at,
            "id": identity,
            "booking_number": f"FC-{identity[:8]}",
            "source_updated_at": booking_date or pulled_at,
            "visibility": "public",
            "full_name": name,
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "sex": None,
            "race": None,
            "booking_date": booking_date or pulled_at,
            "release_date": None,
            "charges": charges,
            "bond_amount": None,
            "bonds": bonds,
            "status": "in_custody",
            "mugshot_url": None,
            "notes": status_note,
        })

    return AdapterResult(source, records)
