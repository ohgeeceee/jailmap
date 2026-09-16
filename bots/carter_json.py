"""Carter County MT — dmxConnect JSON API (staging-only adapter).
Source: https://cartercountysheriff.us/dmxConnect/api/Booking/Read2.php
Official county sheriff API. Privacy: drops dob, address, mugshot fields
(MISSION.md: raw identifiers and photos are never public).
"""
import re
from datetime import datetime, timezone
import httpx
from backend.normalize import normalize

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
            "Accept": "application/json"}
_BASE = "https://cartercountysheriff.us/dmxConnect/api/Booking/Read2.php"


def _assert_authorized(source):
    host = httpx.URL(source["source_url"]).host
    if host != "cartercountysheriff.us":
        raise ValueError("Source endpoint is not authorized")


def _booking_ts(value):
    """Carter returns naive 'YYYY-MM-DDTHH:MM:SS'; attach UTC per codebase convention."""
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.strptime(str(value).strip(), "%Y-%m-%dT%H:%M:%S")
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).isoformat()
    return dt.replace(tzinfo=timezone.utc).isoformat()


def _split_charges(text):
    """Carter separates charges with '<br> &bull; '; split into clean items."""
    if not text:
        return []
    out = []
    for part in re.split(r'<br\s*/?>', text):
        p = re.sub(r'^\s*&bull;\s*', '', part).strip()
        if p:
            out.append(p)
    return out


def fetch(source):
    _assert_authorized(source)
    rows, offset, seen = [], 0, set()
    with httpx.Client(timeout=30, follow_redirects=False, headers=_HEADERS) as client:
        for _ in range(50):
            r = client.get(_BASE, params={"offset": offset, "limit": 100})
            r.raise_for_status()
            data = r.json().get("query", [])
            if not data:
                break
            for b in data:
                key = str(b.get("BookingID") or b.get("BookingNum"))
                if key in seen:
                    continue
                seen.add(key)
                status = "released" if (b.get("ReleaseDate") or "").strip() else "in_custody"
                charges = [
                    {"id": f"{key}-{i}", "description": c[:2000],
                     "statute": None, "severity": None}
                    for i, c in enumerate(_split_charges(b.get("Charges")))
                ]
                rows.append(normalize({
                    "booking_number": str(b.get("BookingNum") or key),
                    "first_name": (b.get("FName") or "").strip(),
                    "last_name": (b.get("LName") or "").strip(),
                    "dob": None,                      # excluded: raw identifier
                    "booking_date": _booking_ts(b.get("BookingDate")),
                    "mugshot_url": None,              # excluded: needs state review
                    "updated_at": _booking_ts(b.get("BookingDate")),
                    "status": status,
                    "charges": charges,
                    "bonds": [],
                }))
            if len(data) < 100:
                break
            offset += 100
    return rows