"""Garfield County, Montana — daily PDF roster adapter.

Source: https://www.garcosheriff.com/PDFs/current_inmates.pdf
Multi-page PDF with recent arrests on page 1, releases on subsequent pages.
Format: "LastName, FirstName MiddleName Age:NN\nGender\nMM/DD/YYYY"
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List
from io import BytesIO

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/pdf,application/octet-stream,*/*",
    "Referer": "https://www.garcosheriff.com/",
}

_INMATE_RE = re.compile(
    r"([A-Za-z][A-Za-z\s\-\']+?),([A-Za-z\s\-\']+?)\s+Age:\d+\s*\n\s*(Male|Female)\s*\n\s*(\d{2}/\d{2}/\d{4})"
)


def _parse_date(raw: str) -> str:
    try:
        dt = datetime.strptime(raw.strip(), "%m/%d/%Y")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return raw


def fetch(source) -> AdapterResult:
    _assert_authorized(source["source_url"])
    pulled_at = datetime.now(timezone.utc).isoformat()

    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        resp = client.get(source["source_url"], headers=_HEADERS)
        resp.raise_for_status()
        pdf_bytes = resp.content

    try:
        import pdfplumber
    except ImportError:
        # Fallback: return empty if pdfplumber not in image
        return AdapterResult(source, [])

    records: List[Dict] = []
    seen_ids = set()

    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            # Page 1 = recent bookings; pages 2+ = releases (we skip releases)
            page = pdf.pages[0]
            text = page.extract_text() or ""
    except Exception:
        return AdapterResult(source, [])

    for m in _INMATE_RE.finditer(text):
        last_name = m.group(1).strip().title()
        first_name = m.group(2).strip().title()
        sex = (m.group(3) or "").strip()
        booking_date = _parse_date(m.group(4))

        full_name = f"{last_name}, {first_name}"
        identity = str(uuid.uuid5(uuid.NAMESPACE_URL, full_name))[:16]
        if identity in seen_ids:
            continue
        seen_ids.add(identity)

        records.append({
            "state": "MT",
            "county": "Garfield",
            "facility": "Garfield County Detention Center",
            "source_url": source["source_url"],
            "source_type": "pdf_roster",
            "pulled_at": pulled_at,
            "id": identity,
            "booking_number": f"GC-{identity[:8]}",
            "source_updated_at": booking_date or pulled_at,
            "visibility": "public",
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "sex": sex,
            "race": None,
            "booking_date": booking_date or pulled_at,
            "release_date": None,
            "charges": [],
            "bond_amount": None,
            "bonds": [],
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
