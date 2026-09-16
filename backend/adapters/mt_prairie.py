"""Prairie County MT jail roster adapter.

ASP.NET WebForms roster: https://www.myr2m.com/PrairieCoRoster/NewInmates.aspx
The page renders the inmate list directly in HTML (not AJAX). Each inmate is
inside a repeating region with indexed span tags: name, race/sex/age, address,
arrest date, agency, release date, and a charges table.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List

import httpx

from backend.adapters.idaho import AdapterResult, _assert_authorized

_URL = "https://www.myr2m.com/PrairieCoRoster/NewInmates.aspx"

_NAME_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_lblName_(\d+)"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_RACE_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_lblRace_(\d+)"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_ADDR_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_lblAddress_(\d+)"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_ARREST_DATE_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_lblArrestDate_(\d+)"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_ARREST_BY_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_lblArrestBy_(\d+)"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_RELEASE_DATE_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_lblReleaseDate_(\d+)"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)
_CHARGE_RE = re.compile(
    r'id="ContentPlaceHolder1_rptListInmates_chargeGrid_\d+_Label1_\d+"[^>]*>([^<]+)</span>',
    re.IGNORECASE,
)

_SEX_RACE_RE = re.compile(r"([A-Z])\s*/\s*([A-Z])\s*/\s*(\d+)")

_DATE_FORMATS = ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y")


def _text(raw: str) -> str:
    return re.sub(r"\s+", " ", unescape(raw or "")).strip()


def _parse_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            if "%H" not in fmt:
                dt = dt.replace(hour=12, minute=0, second=0)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return None


def _parse_race_sex_age(raw: str):
    sex = race = age = None
    m = _SEX_RACE_RE.search(raw or "")
    if m:
        race = m.group(1).upper()
        sex_token = m.group(2).upper()
        sex = {"M": "Male", "F": "Female"}.get(sex_token)
        age = int(m.group(3))
    return race, sex, age


def _parse_entries(page_html: str) -> List[Dict]:
    names = {m[0]: _text(m[1]) for m in _NAME_RE.findall(page_html)}
    races = {m[0]: _text(m[1]) for m in _RACE_RE.findall(page_html)}
    addrs = {m[0]: _text(m[1]) for m in _ADDR_RE.findall(page_html)}
    arrest_dates = {m[0]: _text(m[1]) for m in _ARREST_DATE_RE.findall(page_html)}
    arrest_bys = {m[0]: _text(m[1]) for m in _ARREST_BY_RE.findall(page_html)}
    release_dates = {m[0]: _text(m[1]) for m in _RELEASE_DATE_RE.findall(page_html)}

    # Charges are grouped by inmate index via the table id
    charges_by_idx: Dict[str, List[str]] = {}
    for table_match in re.finditer(
        r'id="ContentPlaceHolder1_rptListInmates_chargeGrid_(\d+)"(.*?)(?:</table>|</div>)',
        page_html,
        re.IGNORECASE | re.DOTALL,
    ):
        idx = table_match.group(1)
        charges = [_text(m) for m in re.findall(
            r'id="ContentPlaceHolder1_rptListInmates_chargeGrid_\d+_Label1_\d+"[^>]*>([^<]+)</span>',
            table_match.group(2), re.IGNORECASE
        )]
        charges_by_idx[idx] = [c for c in charges if c and c != "FAILURE TO APPEAR - FELONY"]

    entries = []
    for idx, full_name in names.items():
        if not full_name:
            continue
        if "," in full_name:
            last, first = [p.strip() for p in full_name.split(",", 1)]
        else:
            parts = full_name.split()
            first = parts[0] if parts else ""
            last = " ".join(parts[1:]) if len(parts) > 1 else ""

        race_raw = races.get(idx, "")
        race, sex, age = _parse_race_sex_age(race_raw)

        entries.append({
            "first_name": first,
            "last_name": last,
            "sex": sex,
            "race": race,
            "age": age,
            "address": addrs.get(idx),
            "booking_date": _parse_date(arrest_dates.get(idx, "")),
            "agency": arrest_bys.get(idx),
            "release_date": _parse_date(release_dates.get(idx, "")),
            "charges": charges_by_idx.get(idx, []),
        })
    return entries


def fetch(source) -> AdapterResult:
    url = source.get("source_url") or _URL
    _assert_authorized(url)
    pulled_at = datetime.now(timezone.utc).isoformat()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
        "Accept": "text/html,application/xhtml+xml",
    }
    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        page_html = response.text

    entries = _parse_entries(page_html)
    records = []
    for i, entry in enumerate(entries):
        booking_number = f"PC-{i:06d}"
        records.append({
            "state": "MT",
            "county": "Prairie",
            "facility": source.get("facility_name", "Prairie County Jail"),
            "source_url": url,
            "source_type": "html_roster",
            "pulled_at": pulled_at,
            "source_id": booking_number,
            "inmate_id": None,
            "booking_number": booking_number,
            "source_updated_at": entry["booking_date"] or pulled_at,
            "visibility": "public",
            "full_name": f"{entry['first_name']} {entry['last_name']}".strip(),
            "first_name": entry["first_name"],
            "last_name": entry["last_name"],
            "dob": None,
            "age": entry["age"],
            "sex": entry["sex"],
            "race": entry["race"],
            "booking_date": entry["booking_date"],
            "release_date": entry["release_date"],
            "charges": [{"source_id": f"CH-{j:03d}", "description": c[:2000],
                         "statute": None, "severity": None}
                        for j, c in enumerate(entry["charges"])],
            "bond_amount": None,
            "bonds": [],
            "status": "in_custody",
            "mugshot_url": None,
            "notes": None,
        })

    return AdapterResult(source, records)
