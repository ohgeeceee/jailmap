"""Evo Gov JSON roster adapter (ID counties using evogov.com)."""
import uuid
import httpx
import re
import json
from datetime import datetime, timezone
from backend.adapters.idaho import AdapterResult, _assert_authorized

def _name_parts(raw: str):
    name = (raw or "").strip()
    if not name:
        return "", ""
    if "," in name:
        last, _, first = name.partition(",")
        return first.strip().title(), last.strip().title()
    parts = name.split()
    if len(parts) >= 2:
        return parts[0].title(), " ".join(parts[1:]).title()
    return "", name

def _parse_date(value: str):
    if not value or not value.strip():
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})", value.strip())
    if m:
        mo, dy, yr, hr, mi = (int(p) for p in m.groups())
        return f"{yr:04d}-{mo:02d}-{dy:02d}T{hr:02d}:{mi:02d}:00Z"
    m2 = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})", value.strip())
    if m2:
        yr, mo, dy, hr, mi = (int(p) for p in m2.groups())
        return f"{yr:04d}-{mo:02d}-{dy:02d}T{hr:02d}:{mi:02d}:00Z"
    return None

def fetch(source) -> AdapterResult:
    _assert_authorized(source["source_url"])
    records = []
    page = 1
    total = None
    pulled_at = datetime.now(timezone.utc).isoformat()
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        while True:
            params = {"page": page, "page_size": 50}
            resp = client.get(source["source_url"], params=params)
            resp.raise_for_status()
            data = resp.json()
            if total is None:
                total = data.get("total", 0)
            for row in data.get("rows", []):
                first, last = _name_parts(row.get("name", ""))
                charges = row.get("charges") or []
                # Dedupe identical charges within a row (vendor sometimes emits dupes)
                seen_charges = set()
                deduped_charges = []
                for c in charges:
                    key = (c.get("case_number", ""), c.get("bond_amount"))
                    if key not in seen_charges:
                        seen_charges.add(key)
                        deduped_charges.append(c)
                charges = deduped_charges
                bonds = []
                for i, c in enumerate(charges):
                    bond_amt = c.get("bond_amount")
                    bonds.append({
                        "source_id": str(uuid.uuid5(uuid.NAMESPACE_URL, c.get("case_number", "") + str(c.get("bond_amount", "")) + f"-{i}"))[:16],
                        "amount": float(bond_amt) if bond_amt else None,
                        "type": "bond",
                        "status": "set",
                    })
                # Stable unique identity from name + date + sorted charge descriptions
                identity_parts = [
                    row.get("name", ""),
                    row.get("booked", ""),
                    json.dumps([c.get("case_number", "") for c in charges], sort_keys=True),
                ]
                identity = str(uuid.uuid5(uuid.NAMESPACE_URL, "|".join(identity_parts)))[:16]
                records.append({
                    "booking_number": identity,
                    "first_name": first,
                    "last_name": last,
                    "id": identity,
                    "booking_date": _parse_date(row.get("booked", "")) or pulled_at,
                    "source_updated_at": pulled_at,
                    "status": "in_custody",
                    "visibility": "public",
                    "dob": None,
                    "mugshot_url": row.get("photo_url"),
                    "charges": [{
                        "source_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "|" + identity + c.get("case_number", "") + str(c.get("bond_amount", "")) + f"-{i}"))[:16],
                        "description": c.get("case_number", "")[:2000],
                        "statute": None,
                        "severity": None,
                    } for i, c in enumerate(charges)],
                    "bonds": bonds,
                })
            if len(records) >= total or not data.get("rows"):
                break
            page += 1
    return AdapterResult(source, records)
