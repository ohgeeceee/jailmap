"""Kentucky Fayette County Jail adapter.

Source: https://lookup.fayettesheriff.org/inmatelookup.php
Static HTML table with 344+ records.

Columns: Last Name, First Name, Middle Name, Suffix, DOB, Race, Sex, Start Date
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import re
import html as html_mod


class AdapterResult:
    """Simple wrapper so ingest.py defensive visibility code works."""
    def __init__(self, records: List[Dict]):
        self.records = records


def fetch(source: Optional[Dict] = None) -> AdapterResult:
    """Fetch the roster from the static HTML table."""
    import httpx

    url = (source or {}).get('source_url', 'https://lookup.fayettesheriff.org/inmatelookup.php')
    resp = httpx.get(url, timeout=60)
    resp.raise_for_status()
    html = resp.text

    records = parse_html(html, source or {})
    return AdapterResult(records)


def parse(source: Optional[Dict] = None) -> AdapterResult:
    """Compatibility alias for fetch()."""
    return fetch(source)


def parse_html(html: str, source: Dict) -> List[Dict]:
    """Parse the static HTML table into inmate records."""
    records = []

    # Rows have class="inmate-row"
    rows = re.findall(r'<tr[^>]*class="inmate-row"[^>]*>(.*?)</tr>', html, re.DOTALL)
    for row in rows:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(tds) < 8:
            continue

        # Clean values: remove HTML tags, decode entities, strip whitespace
        vals = [_clean(td) for td in tds]

        # Columns: 0=Last, 1=First, 2=Middle, 3=Suffix, 4=DOB, 5=Race, 6=Sex, 7=Start Date
        last_name = vals[0]
        first_name = vals[1]
        middle_name = vals[2]
        suffix = vals[3]
        dob_raw = vals[4]
        race = vals[5]
        sex = vals[6]
        start_date = vals[7]

        # Skip if no name
        if not last_name or not first_name:
            continue

        # Parse DOB
        dob = None
        dob_precision = None
        if dob_raw:
            dob_parsed = _parse_date(dob_raw)
            if dob_parsed:
                dob = dob_parsed
                dob_precision = 'day'

        # Parse booking date
        booking_date = None
        booking_precision = None
        if start_date:
            bd_parsed = _parse_date(start_date)
            if bd_parsed:
                booking_date = bd_parsed
                booking_precision = 'day'

        record = {
            'booking_number': f'KY-FAYETTE-{last_name}-{first_name}-{start_date}',
            'first_name': first_name,
            'last_name': last_name,
            'middle_name': middle_name,
            'suffix': suffix,
            'dob': dob,
            'dob_precision': dob_precision,
            'race': race,
            'sex': sex,
            'booking_date': booking_date,
            'booking_date_precision': booking_precision,
            'booking_timezone': 'America/New_York',
            'source_updated_at': datetime.now(timezone.utc).isoformat(),
            'visibility': 'public',
        }
        records.append(record)

    return records


def _clean(text: str) -> str:
    """Strip HTML tags, decode entities, and trim whitespace."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    return text.strip()


def _parse_date(value: str) -> Optional[str]:
    """Try to parse a date string into YYYY-MM-DD format."""
    if not value:
        return None

    # Common formats
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    return None
