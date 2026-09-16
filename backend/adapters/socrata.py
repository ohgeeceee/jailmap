"""Socrata open-data portal adapter.

Socrata-backed portals publish a documented JSON API (`/resource/<dataset>.json`)
with SoQL query support. That makes them the highest-quality class of source on
JailMap: no scraping, no HTML drift, stable identifiers, and an explicit row count.

Two entry points:

* `discover(domain)` — asks the Socrata Discovery API which datasets on a portal
  look like custody/booking data. Used by source scouting, not by ingest.
* `fetch(source)` — pulls a dataset into the staging contract.

Staging-only, like every adapter added by the national rollout. `fetch()` returns
the staging row shape, so imperfect rows are flagged in `records.staged_bookings`
rather than published. Nothing here can put a person in the public index.

Bounded: page size, page count, total rows and response size are all capped, and
the egress allowlist is enforced through the shared helper.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _assert_authorized

PAGE_SIZE = 1_000
MAX_PAGES = 20
MAX_ROWS = 20_000

# Socrata field names are snake_case already; map them onto our contract. Matched
# after normalising to lowercase alphanumerics, so "booking_date" and "BookingDate"
# both land.
FIELD_ALIASES: Dict[str, str] = {
    'bookingnumber': 'booking_number', 'bookingno': 'booking_number',
    'bookingid': 'booking_number', 'inmatenumber': 'booking_number',
    'inmateid': 'booking_number', 'jailid': 'booking_number',
    'casenumber': 'booking_number', 'recordid': 'booking_number',
    'lastname': 'last_name', 'lname': 'last_name',
    'firstname': 'first_name', 'fname': 'first_name',
    'fullname': 'full_name', 'inmatename': 'full_name', 'name': 'full_name',
    'bookingdate': 'booking_date', 'arrestdate': 'booking_date',
    'datebooked': 'booking_date', 'intakedate': 'booking_date',
    'admitdate': 'booking_date', 'custodydate': 'booking_date',
    'releasedate': 'release_date',
    'charge': 'charges', 'charges': 'charges', 'offense': 'charges',
    'offensedescription': 'charges', 'description': 'charges',
    'chargedescription': 'charges', 'charge_desc': 'charges',
    'offensecharge': 'charges', 'statute': 'charges',
    'bond': 'bond_amount', 'bondamount': 'bond_amount', 'bail': 'bond_amount',
    'totalbond': 'bond_amount',
    'status': 'status', 'custodystatus': 'status',
    'sex': 'sex', 'gender': 'sex', 'race': 'race', 'age': 'age',
    'dob': 'dob', 'dateofbirth': 'dob',
    'facility': 'facility', 'facilityname': 'facility',
}

STATUS_MAP = {
    'incustody': 'in_custody', 'inmate': 'in_custody', 'current': 'in_custody',
    'active': 'in_custody', 'held': 'in_custody',
    'released': 'released', 'discharged': 'released', 'out': 'released',
    'transferred': 'transferred',
}

DISCOVERY_URL = 'https://api.us.socrata.com/api/catalog/v1'


def _norm(key: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(key).lower())


def _clean(value) -> str:
    if value is None:
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()


def map_record(raw: Dict, source: Dict, pulled_at: str) -> Optional[Dict]:
    """Map one Socrata record onto the staging contract."""
    fields: Dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, (dict, list)):
            # Socrata location/point columns are objects; keep them out of the text map.
            continue
        target = FIELD_ALIASES.get(_norm(key))
        if target and target not in fields:
            fields[target] = _clean(value)

    last = fields.get('last_name', '')
    first = fields.get('first_name', '')
    full = fields.get('full_name', '')
    if not full and (last or first):
        full = f'{last}, {first}'.strip(', ')
    if not full:
        return None
    status = STATUS_MAP.get(_norm(fields.get('status', '')))
    booking_date = _iso(fields.get('booking_date'))
    return {
        'state': source.get('state', ''),
        'county': source.get('county', ''),
        'facility': fields.get('facility') or source.get('facility_name', ''),
        'source_url': source.get('source_url', ''),
        'source_type': 'socrata_open_data',
        'pulled_at': pulled_at,
        'inmate_id': None,
        'booking_number': fields.get('booking_number') or None,
        'full_name': full,
        'first_name': first,
        'last_name': last,
        'dob': _iso(fields.get('dob')),
        'age': int(fields['age']) if fields.get('age', '').isdigit() else None,
        'sex': fields.get('sex') or None,
        'race': fields.get('race') or None,
        'booking_date': booking_date,
        'source_updated_at': booking_date or pulled_at,
        'status': status,
        'release_date': _iso(fields.get('release_date')),
        'charges': ([{'source_id': 'c1', 'description': fields['charges'][:2000],
                      'statute': None, 'severity': None}]
                    if fields.get('charges') else []),
        'bonds': [],
        'mugshot_url': None,
        'notes': None,
    }


def _iso(value: str) -> Optional[str]:
    """Socrata returns ISO-8601 already; accept a date-only form too."""
    text = _clean(value)
    if not text:
        return None
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        return f'{text}T12:00:00Z'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}T.*', text):
        return text if text.endswith('Z') or '+' in text else text + 'Z'
    return None


def dataset_url(domain: str, dataset: str) -> str:
    return f'https://{domain}/resource/{dataset}.json'


def fetch(source) -> List[Dict]:
    """Pull every page of a Socrata dataset into the staging contract."""
    import httpx
    base = source['source_url']
    _assert_authorized(base)
    if '/resource/' not in base:
        raise ValueError('Socrata source_url must point at a /resource/<id> dataset')
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for page in range(MAX_PAGES):
            response = client.get(base, params={
                '$limit': PAGE_SIZE,
                '$offset': page * PAGE_SIZE,
                '$order': ':id',
            })
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError('Socrata response was not a record list')
            for raw in payload:
                if not isinstance(raw, dict):
                    continue
                mapped = map_record(raw, dict(source), pulled_at)
                if mapped:
                    records.append(mapped)
                if len(records) >= MAX_ROWS:
                    return records
            if len(payload) < PAGE_SIZE:
                break
    return records


def parse(source) -> AdapterResult:
    return AdapterResult(source, fetch(source))


def discover(domain: str, query: str = 'inmate') -> List[Dict]:
    """Ask the Socrata catalog which datasets on `domain` look like custody data.

    Scouting helper — call it from a research pass, never from the ingest loop.
    """
    import httpx
    with httpx.Client(timeout=25, follow_redirects=True) as client:
        response = client.get(DISCOVERY_URL, params={
            'domains': domain, 'q': query, 'limit': 20,
            'only': 'dataset', 'search_context': domain,
        })
        response.raise_for_status()
        payload = response.json()
    out = []
    for result in payload.get('results', []):
        resource = result.get('resource') or {}
        out.append({
            'domain': domain,
            'dataset': resource.get('id'),
            'name': resource.get('name'),
            'updated': resource.get('updatedAt'),
            'url': dataset_url(domain, resource.get('id') or ''),
        })
    return out
