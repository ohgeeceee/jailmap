from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import httpx

from backend.adapters.idaho import AdapterResult


def fetch(source) -> AdapterResult:
    """Fetch roster from Tyler Odyssey PublicSafety portal."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    seen_ids = set()

    with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
        resp = client.get(source['source_url'], params={'Name': '', 'InCustody': 'True'})
        resp.raise_for_status()

        html = resp.text
        tbody_start = html.find('<tbody>')
        tbody_end = html.find('</tbody>', tbody_start) if tbody_start != -1 else -1
        if tbody_start == -1 or tbody_end == -1:
            return AdapterResult(source, [])

        tbody = html[tbody_start:tbody_end]
        name_pattern = re.compile(r'<td class="Name"><a[^>]*>([^<]+)</a></td>\s*<td class="SubjectNumber">([^<]+)</td>\s*<td class="InCustody">([^<]+)</td>')

        for match in name_pattern.finditer(tbody):
            name = match.group(1).strip()
            subject_number = match.group(2).strip()
            custody = match.group(3).strip().lower()

            if custody not in ('yes', 'true'):
                continue

            last, first = '', ''
            if ',' in name:
                parts = name.split(',', 1)
                last = parts[0].strip().title()
                first = parts[1].strip().title() if len(parts) > 1 else ''
            else:
                parts = name.split()
                if len(parts) > 1:
                    last = parts[-1].title()
                    first = ' '.join(parts[:-1]).title()
                elif parts:
                    last = parts[0].title()

            identity = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{subject_number}|{name}"))[:16]
            if identity in seen_ids:
                continue
            seen_ids.add(identity)

            records.append({
                'booking_number': subject_number or f"TYLER-{identity}",
                'first_name': first,
                'last_name': last,
                'source_id': identity,
                'booking_date': pulled_at,
                'status': 'in_custody',
                'visibility': 'public',
                'dob': None,
                'charges': [],
                'bonds': [],
            })

    return AdapterResult(source, records)
