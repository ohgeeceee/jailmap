"""Evo Gov JSON roster adapter (ID counties using evogov.com).

Cassia County's /jail-roster-data/roster/ returns a paginated JSON:
{"dataset":"roster","total":N,"page":1,"page_size":25,"rows":[...]}

Each row: booking_id, name, sex, race, age, booked, charges, photo_url
"""
import httpx
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
    # format: "06/03/2026 09:04"
    import re
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})", value.strip())
    if m:
        mo, dy, yr, hr, mi = (int(p) for p in m.groups())
        return f"{yr:04d}-{mo:02d}-{dy:02d}T{hr:02d}:{mi:02d}:00Z"
    # fallback: "2026-06-03 09:04"
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
                bonds = []
                for c in charges:
                    bond_amt = c.get("bond_amount")
                    bonds.append({
                        "source_id": str(hash(c.get("case_number", "")))[:12],
                        "amount": float(bond_amt) if bond_amt else None,
                        "type": "bond",
                        "status": "set",
                    })
                records.append({
                    "state": source.get("state", ""),
                    "county": source.get("county", ""),
                    "facility": source.get("facility_name", ""),
                    "source_url": source.get("source_url", ""),
                    "source_type": "evo_json",
                    "pulled_at": pulled_at,
                    "inmate_id": None,
                    "booking_number": row.get("booking_id") or f"EV-{len(records)}",
                    "full_name": row.get("name", "").strip(),
                    "first_name": first,
                    "last_name": last,
                    "dob": None,
                    "age": row.get("age"),
                    "sex": row.get("sex"),
                    "race": row.get("race"),
                    "booking_date": _parse_date(row.get("booked", "")),
                    "source_updated_at": _parse_date(row.get("booked", "")) or pulled_at,
                    "status": "in_custody",
                    "charges": [{
                        "source_id": str(hash(c.get("case_number", "")))[:12],
                        "description": c.get("case_number", "")[:2000],
                        "statute": None,
                        "severity": None,
                    } for c in charges],
                    "bonds": bonds,
                    "release_date": None,
                    "mugshot_url": row.get("photo_url"),
                    "notes": None,
                })
            if len(records) >= total or not data.get("rows"):
                break
            page += 1
    return AdapterResult(source, records)
