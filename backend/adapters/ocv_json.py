from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
    "Accept": "application/json,text/html,*/*;q=0.8",
}

OCV_ID_RE = re.compile(r"ocvapps/([a-zA-Z0-9]+)/inmates\.json")
OCV_SITE_ID_RE = re.compile(r"data-site-id=[\"']([a-zA-Z0-9]+)[\"']")
OCV_DIRECT_RE = re.compile(r"https?://(?:cdn\.myocv\.com|myocv\.s3\.amazonaws\.com)/ocvapps/([a-zA-Z0-9]+)/inmates\.json")
CHARGE_RE = re.compile(r"charge[s]?[\"']?\s*[:=]\s*[\"']([^\"']+)", re.IGNORECASE)


def _parse_ocv_date(date_obj) -> Optional[str]:
    """OCV dates can be unix timestamps or ISO strings."""
    if isinstance(date_obj, dict):
        sec = date_obj.get("sec")
        if sec:
            try:
                return datetime.fromtimestamp(sec, tz=timezone.utc).isoformat()
            except (ValueError, OSError):
                pass
    if isinstance(date_obj, (int, float)):
        try:
            return datetime.fromtimestamp(date_obj, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            pass
    if isinstance(date_obj, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(date_obj, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.isoformat()
            except ValueError:
                continue
    return None


def _extract_site_id(html: str, source_url: str) -> Optional[str]:
    """Extract OCV site ID from page HTML or URL."""
    # Direct JSON URL in page
    direct = OCV_DIRECT_RE.search(html)
    if direct:
        return direct.group(1)
    # data-site-id attribute
    attr = OCV_SITE_ID_RE.search(html)
    if attr:
        return attr.group(1)
    # ocvapps pattern in scripts
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    for script in scripts:
        match = OCV_ID_RE.search(script)
        if match:
            return match.group(1)
    return None


def fetch(source) -> AdapterResult:
    # OCV adapter fetches from CDN, not the county site, so skip egress check
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        resp = client.get(source["source_url"], headers=HEADERS)
        resp.raise_for_status()
        html = resp.text

    site_id = _extract_site_id(html, source["source_url"])
    if not site_id:
        return AdapterResult(source, [])

    # Fetch inmates JSON
    json_url = f"https://cdn.myocv.com/ocvapps/{site_id}/inmates.json"
    try:
        with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
            resp = client.get(json_url, headers={**HEADERS, "Referer": source["source_url"]})
            resp.raise_for_status()
            inmates = resp.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        # Try alternate URL
        try:
            json_url = f"https://myocv.s3.amazonaws.com/ocvapps/{site_id}/inmates.json"
            with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
                resp = client.get(json_url, headers={**HEADERS, "Referer": source["source_url"]})
                resp.raise_for_status()
                inmates = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            return AdapterResult(source, [])

    if not isinstance(inmates, list):
        return AdapterResult(source, [])

    for raw in inmates:
        if not isinstance(raw, dict):
            continue
        first = (raw.get("firstName") or raw.get("first_name") or "").strip().title()
        last = (raw.get("lastName") or raw.get("last_name") or "").strip().title()
        title = (raw.get("title") or raw.get("full_name") or "").strip()
        if not first and not last and title:
            if "," in title:
                parts = title.split(",", 1)
                last = parts[0].strip().title()
                first = parts[1].strip().title()
            else:
                parts = title.split(None, 1)
                first = parts[0].title() if parts else ""
                last = parts[1].title() if len(parts) > 1 else ""

        booking_number = str(raw.get("bookingNumber") or raw.get("booking_number") or raw.get("id") or raw.get("_id", {}).get("$id", ""))
        booking_date = _parse_ocv_date(raw.get("date") or raw.get("booking_date"))

        charges = []
        raw_charges = raw.get("charges") or raw.get("charge") or []
        if isinstance(raw_charges, str):
            raw_charges = [{"source_id": "c1", "description": raw_charges[:2000]}]
        elif isinstance(raw_charges, list):
            for i, c in enumerate(raw_charges[:50]):
                if isinstance(c, str):
                    charges.append({"source_id": f"c{i+1}", "description": c[:2000], "statute": None, "severity": None})
                elif isinstance(c, dict):
                    desc = c.get("description") or c.get("charge") or c.get("statute") or ""
                    charges.append({
                        "source_id": str(c.get("source_id") or c.get("id") or f"c{i+1}"),
                        "description": str(desc)[:2000],
                        "statute": str(c.get("statute") or "") or None,
                        "severity": str(c.get("degree") or c.get("severity") or "") or None,
                    })

        bonds = []
        raw_bonds = raw.get("bonds") or raw.get("bond") or []
        if isinstance(raw_bonds, str):
            try:
                amt = float(raw_bonds.replace(",", "").replace("$", ""))
                bonds.append({"source_id": "b1", "amount": amt, "type": "bond", "status": "set"})
            except ValueError:
                pass
        elif isinstance(raw_bonds, list):
            for i, b in enumerate(raw_bonds[:20]):
                if isinstance(b, (int, float)):
                    bonds.append({"source_id": f"b{i+1}", "amount": float(b), "type": "bond", "status": "set"})
                elif isinstance(b, dict):
                    amt = b.get("amount") or b.get("bond_amount")
                    if amt is not None:
                        try:
                            bonds.append({
                                "source_id": str(b.get("source_id") or b.get("id") or f"b{i+1}"),
                                "amount": float(amt),
                                "type": str(b.get("type") or "bond"),
                                "status": str(b.get("status") or "set"),
                            })
                        except (ValueError, TypeError):
                            pass

        identity = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{booking_number}|{first}|{last}|{booking_date}",
        ))[:16]

        records.append({
            "state": raw.get("state") or source.get("state", ""),
            "county": raw.get("county") or source.get("county", ""),
            "facility": raw.get("facility") or source.get("facility_name", ""),
            "source_url": source["source_url"],
            "source_type": "ocv_portal",
            "pulled_at": pulled_at,
            "id": identity,
            "booking_number": booking_number or identity,
            "source_updated_at": booking_date or pulled_at,
            "visibility": "public",
            "full_name": f"{first} {last}".strip(),
            "first_name": first,
            "last_name": last,
            "booking_date": booking_date or pulled_at,
            "release_date": None,
            "charges": charges or [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}],
            "bonds": bonds,
            "dob": _parse_ocv_date(raw.get("dob") or raw.get("dateOfBirth") or raw.get("date_of_birth")),
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
