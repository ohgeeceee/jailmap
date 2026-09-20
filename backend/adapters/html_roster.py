"""Generic HTML roster-table adapter.

One parser for the long tail of county sheriff sites that publish a plain HTML
table. The 2026-09-14 national census found `html_roster` to be the second-largest
directly-adaptable class (72 of 2,648 domains, and more behind link following), and
every one of them was bespoke. This module removes the need for a new file per county.

Design constraints:

* **Staging-only by design.** `fetch()` returns the staging row contract, not the
  strict public contract. `prepare_staging_rows()` flags imperfect rows instead of
  rejecting them, so a generic parser with imperfect data lands in
  `records.staged_bookings` rather than in the public index. Nothing here can
  publish a person's record; a human promotes it.
* **No new dependencies.** The container has no bs4/lxml, so this uses stdlib
  `html.parser`. Do not add a parsing library for this.
* **No invented facts.** If a table has no status column, `status` stays None rather
  than being assumed `in_custody`. Guessing custody status on someone's record is
  the exact failure this project cannot afford.
* **Bounded.** Response size and row count are capped, and the egress allowlist
  (`SOURCE_ALLOWED_HOSTS`) is enforced via the shared helper.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _assert_authorized, _fetch_html

MAX_BYTES = 3_000_000
MAX_ROWS = 2_000
MIN_CELLS = 2

# Header token -> canonical field. Matched on a normalised header cell, exact first
# then substring ("Booking Date" -> "bookingdate").
COLUMN_ALIASES: Dict[str, str] = {
    'bookingnumber': 'booking_number', 'bookingno': 'booking_number',
    'booking': 'booking_number', 'bookno': 'booking_number',
    'casenumber': 'booking_number', 'caseno': 'booking_number',
    'inmateid': 'booking_number', 'jailid': 'booking_number',
    'controlnumber': 'booking_number', 'refno': 'booking_number',
    'lastname': 'last_name', 'last': 'last_name', 'lname': 'last_name',
    'surname': 'last_name',
    'firstname': 'first_name', 'first': 'first_name', 'fname': 'first_name',
    'givenname': 'first_name',
    'name': 'full_name', 'inmatename': 'full_name', 'fullname': 'full_name',
    'inmate': 'full_name', 'person': 'full_name', 'defendant': 'full_name',
    'bookingdate': 'booking_date', 'bookdate': 'booking_date',
    'arrestdate': 'booking_date', 'datebooked': 'booking_date',
    'dateofbooking': 'booking_date', 'incarcerationdate': 'booking_date',
    'custodydate': 'booking_date', 'intakedate': 'booking_date',
    'admitted': 'booking_date', 'admitdate': 'booking_date',
    'releasedate': 'release_date', 'dateofrelease': 'release_date',
    'released': 'release_date',
    'charge': 'charges', 'charges': 'charges', 'offense': 'charges',
    'offenses': 'charges', 'offensecharge': 'charges', 'hold': 'charges',
    'holds': 'charges', 'holdreason': 'charges', 'holdreasons': 'charges',
    'description': 'charges', 'crime': 'charges', 'statute': 'charges',
    'bond': 'bond_amount', 'bonds': 'bond_amount', 'bail': 'bond_amount',
    'bondamount': 'bond_amount', 'totalbond': 'bond_amount',
    'totalbail': 'bond_amount', 'amount': 'bond_amount',
    'status': 'status', 'custody': 'status', 'custodystatus': 'status',
    'currentstatus': 'status', 'inmatestatus': 'status',
    'dob': 'dob', 'dateofbirth': 'dob', 'birthdate': 'dob',
    'sex': 'sex', 'gender': 'sex',
    'race': 'race', 'age': 'age',
    'facility': 'facility', 'housing': 'facility', 'location': 'facility',
    'pod': 'facility',
}

# A roster table must carry a person identity. Without one it is a stats table or
# a navigation widget, and harvesting it would invent people.
IDENTITY_FIELDS = ('full_name', 'last_name')

STATUS_MAP = {
    'in custody': 'in_custody', 'incustody': 'in_custody', 'inmate': 'in_custody',
    'current': 'in_custody', 'held': 'in_custody', 'active': 'in_custody',
    'released': 'released', 'out': 'released', 'discharged': 'released',
    'bonded': 'released', 'transferred': 'transferred',
}


class _TableExtractor(HTMLParser):
    """Collects HTML tables as lists of rows of cell text.

    Deliberately simple: rowspan/colspan are ignored rather than emulated. A cell
    that spans columns will shift the row, which is why a row is accepted only when
    it has at least as many cells as the header has mapped columns.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: List[List[List[str]]] = []
        self._depth = 0
        self._rows: List[List[str]] = []
        self._row: List[str] = []
        self._cell: List[str] = []
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self._depth += 1
            if self._depth == 1:
                self._rows = []
        elif tag == 'tr' and self._depth:
            self._row = []
        elif tag in ('td', 'th') and self._depth:
            self._cell = []
            self._in_cell = True
        elif tag == 'br' and self._in_cell:
            self._cell.append(' ')

    def handle_endtag(self, tag):
        if tag == 'table' and self._depth:
            self._depth -= 1
            if self._depth == 0:
                if self._rows:
                    self.tables.append(self._rows)
                self._rows = []
        elif tag in ('td', 'th') and self._depth and self._in_cell:
            self._row.append(_clean(' '.join(self._cell)))
            self._in_cell = False
        elif tag == 'tr' and self._depth:
            if any(cell for cell in self._row):
                self._rows.append(self._row)
            self._row = []

    def handle_data(self, data):
        if self._in_cell:
            self._cell.append(data)


def _clean(value: Optional[str]) -> str:
    if not value:
        return ''
    return re.sub(r'\s+', ' ', unescape(str(value))).strip()


# Patterns that never belong in a person's name. When a cell matches one of
# these, the row is UI chrome — not a roster entry.
_NAME_BLOCKLIST = (
    # URLs and web addresses
    re.compile(r'^https?://'),
    re.compile(r'^www\.'),
    # UI action verbs at start of cell
    re.compile(r'^(enter|select|choose|type|input)\b', re.I),
    re.compile(r'^(view|click|tap|swipe|scroll|drag)\b', re.I),
    re.compile(r'^(search|filter|sort|login|sign)\b', re.I),
    re.compile(r'^(about|information|details|overview|summary)\b', re.I),
    re.compile(r'^(building|property|land data)\b', re.I),
    re.compile(r'^(record|records|inmate details|record searches)\b', re.I),
    re.compile(r'^(navigation|menu|nav|footer|header|sidebar)\b', re.I),
    re.compile(r'^(main|home|back|next|previous)\b', re.I),
    re.compile(r'^(coordinator|contact|sar coordinator)\b', re.I),
    re.compile(r'^street name', re.I),
    # Status counters and UI text anywhere in cell
    re.compile(r'live feed', re.I),
    re.compile(r'active bookings', re.I),
    re.compile(r'updates every', re.I),
    re.compile(r'willyweather\.com'),
    # Labels ending with colon ("Enter Tax Year :", "Select Identifier:")
    re.compile(r':\s*$'),
    # Timestamp pattern
    re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'),
    # Form field labels at start
    re.compile(r'^(value|amount|total)\s*:?\s*$', re.I),
    # Job title followed by colon and name: "SAR Coordinator: Joe",
    # "Tax Administrator: Jane", "Director: Smith"
    re.compile(r'(coordinator|administrator|director|manager|officer)\s*:\s*\w', re.I),
    # State abbreviation followed by county info in the name cell itself
    re.compile(r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b.*\b(County|Jail|Facility|Detention)\b', re.I),
    # Common single-word UI labels that are never a person's name
    re.compile(r'^(land|their|our|your|my|its|this|that|these|those|there|here|tax rates|inmate|booking)$', re.I),
    # Tax-related form labels
    re.compile(r'^tax\s', re.I),
    # Status words that adapters sometimes put in the name field
    re.compile(r'^(deceased|et|inactive|active|transfered|transferred|released|arrested|inmate|detainee)\b', re.I),
)


def _is_valid_name(text: str) -> bool:
    """Return False if a cell is UI chrome rather than a person's name."""
    if not text:
        return False
    cleaned = _clean(text)
    if not cleaned:
        return False
    # A real name is short. Form labels and UI text tend to be long.
    if len(cleaned) > 80:
        return False
    for pattern in _NAME_BLOCKLIST:
        if pattern.search(cleaned):
            return False
    return True


def _norm_header(cell: str) -> str:
    return re.sub(r'[^a-z0-9]', '', _clean(cell).lower())


def _map_columns(header_cells: List[str]) -> Dict[str, int]:
    """Map canonical field -> column index. Exact alias match wins over substring."""
    mapping: Dict[str, int] = {}
    for index, cell in enumerate(header_cells):
        key = _norm_header(cell)
        if not key:
            continue
        field = COLUMN_ALIASES.get(key)
        if field is None:
            for alias, candidate in COLUMN_ALIASES.items():
                if alias in key:
                    field = candidate
                    break
        if field and field not in mapping:
            mapping[field] = index
    return mapping


def _split_name(full_name: str, mapping: Dict[str, int], cells: List[str]) -> tuple:
    """Return (first, last). Handles 'Last, First M' and 'First Last'."""
    first = cells[mapping['first_name']] if 'first_name' in mapping and mapping['first_name'] < len(cells) else ''
    last = cells[mapping['last_name']] if 'last_name' in mapping and mapping['last_name'] < len(cells) else ''
    if not first and not last and full_name:
        if ',' in full_name:
            last_part, _, first_part = full_name.partition(',')
            return _clean(first_part), _clean(last_part)
        pieces = full_name.split()
        if len(pieces) >= 2:
            return pieces[0], ' '.join(pieces[1:])
        return '', full_name
    return first, last


def _parse_date(value: str) -> Optional[str]:
    """Best-effort ISO-8601. Returns None on anything ambiguous rather than guessing."""
    text = _clean(value)
    if not text:
        return None
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        return f'{text}T12:00:00Z'
    match = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if match:
        month, day, year = (int(part) for part in match.groups())
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f'{year:04d}-{month:02d}-{day:02d}T12:00:00Z'
    return None


def _parse_amount(value: str) -> Optional[float]:
    text = _clean(value)
    if not text:
        return None
    match = re.search(r'([\d,]+(?:\.\d{2})?)', text.replace('$', ''))
    if not match:
        return None
    try:
        return float(match.group(1).replace(',', ''))
    except ValueError:
        return None


def _status(value: str) -> Optional[str]:
    text = _norm_header(value)
    if not text:
        return None
    for key, mapped in STATUS_MAP.items():
        if _norm_header(key) in text:
            return mapped
    return None


def parse_html(html: str, source: Dict) -> List[Dict]:
    """Extract roster rows from every table carrying a person identity column."""
    extractor = _TableExtractor()
    extractor.feed(html[:MAX_BYTES])
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    seen_rows = set()
    for table in extractor.tables:
        if len(table) < 2:
            continue
        mapping = _map_columns(table[0])
        if not any(field in mapping for field in IDENTITY_FIELDS):
            continue
        for cells in table[1:]:
            if len(cells) < MIN_CELLS or len(cells) < len(mapping):
                continue
            row = _row_from_cells(cells, mapping, source, pulled_at)
            if row:
                # Deduplicate rows within the same parse (repeated rows across pages/sections)
                dedup_key = (row['booking_number'], row['booking_date'], row['full_name'])
                if dedup_key in seen_rows:
                    continue
                seen_rows.add(dedup_key)
                records.append(row)
            if len(records) >= MAX_ROWS:
                return records
    return records


def _row_from_cells(cells: List[str], mapping: Dict[str, int], source: Dict,
                    pulled_at: str) -> Optional[Dict]:
    def cell(field: str) -> str:
        index = mapping.get(field)
        return _clean(cells[index]) if index is not None and index < len(cells) else ''

    full_name = cell('full_name')
    first, last = _split_name(full_name, mapping, cells)
    if not (full_name or first or last):
        return None
    # A header row repeated between tbody sections looks like data; drop it.
    if _norm_header(full_name or last) in COLUMN_ALIASES:
        return None
    # UI chrome masquerading as a name: "Enter Taxpayer...", "View Inmate
    # Details", URLs, timestamps, etc. — reject the row entirely.
    name_source = full_name or last or first
    if not _is_valid_name(name_source):
        return None

    booking_date = _parse_date(cell('booking_date'))
    charges_text = cell('charges')
    bond_amount = _parse_amount(cell('bond_amount'))
    return {
        'state': source.get('state', ''),
        'county': source.get('county', ''),
        'facility': cell('facility') or source.get('facility_name', ''),
        'source_url': source.get('source_url', ''),
        'source_type': 'html_roster',
        'pulled_at': pulled_at,
        'inmate_id': None,
        'booking_number': cell('booking_number') or None,
        'full_name': full_name or _clean(f'{last}, {first}'.strip(', ')),
        'first_name': first,
        'last_name': last,
        'dob': _parse_date(cell('dob')),
        'age': int(cell('age')) if cell('age').isdigit() else None,
        'sex': cell('sex') or None,
        'race': cell('race') or None,
        'booking_date': booking_date,
        'source_updated_at': booking_date or pulled_at,
        'status': _status(cell('status')),
        'charges': ([{'source_id': 'c1', 'description': charges_text[:2000],
                      'statute': None, 'severity': None}]
                    if charges_text else []),
        'bonds': ([{'source_id': 'b1', 'amount': bond_amount, 'type': 'bond',
                    'status': 'set'}] if bond_amount is not None else []),
        'release_date': _parse_date(cell('release_date')),
        'mugshot_url': None,
        'notes': None,
    }


def fetch(source) -> List[Dict]:
    """Adapter entry point. Staging-only: returns rows for records.staged_bookings."""
    _assert_authorized(source['source_url'])
    content = _fetch_html(source['source_url'])
    if len(content) > MAX_BYTES:
        raise ValueError('Source page too large')
    return parse_html(content.decode('utf-8', errors='ignore'), dict(source))


def parse(source) -> AdapterResult:
    return AdapterResult(source, fetch(source))


class PlaywrightHTMLRosterAdapter:
    """JS-rendered roster adapter using Playwright/Chromium.

    Use this for pages that require JavaScript to render their inmate table.
    The adapter navigates to source_url in headless Chromium, waits for table
    rows to appear, then passes the rendered HTML to the shared parse_html().

    For search-form pages (no data until form is submitted), set
    `submit_selector` or leave empty to auto-detect and submit the first form
    with an <input type="submit">.
    """

    def __init__(self, wait_for: str = 'table tbody tr', timeout_ms: int = 30000,
                 max_bytes: int = MAX_BYTES, submit_selector: str = ''):
        self.wait_for = wait_for
        self.timeout_ms = timeout_ms
        self.max_bytes = max_bytes
        self.submit_selector = submit_selector

    def fetch(self, source: Dict) -> List[Dict]:
        """Fetch and parse a JS-rendered roster page."""
        from playwright.sync_api import sync_playwright

        url = source.get('source_url', '')
        _assert_authorized(url)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox',
                      '--disable-dev-shm-usage']
            )
            page = browser.new_page()
            page.set_default_timeout(self.timeout_ms)
            page.goto(url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)

            # Auto-detect and submit search form if no rows visible
            rows = page.query_selector_all(self.wait_for)
            if not rows:
                if self.submit_selector:
                    btn = page.query_selector(self.submit_selector)
                    if btn:
                        btn.click()
                        page.wait_for_timeout(4000)
                else:
                    # Try the first submit button
                    btn = page.query_selector(
                        'input[type="submit"], button[type="submit"]'
                    )
                    if btn:
                        btn.click()
                        page.wait_for_timeout(4000)

            try:
                page.wait_for_selector(self.wait_for,
                                       timeout=self.timeout_ms)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            html = page.evaluate('document.documentElement.outerHTML')
            browser.close()

        if len(html) > self.max_bytes:
            raise ValueError('Rendered page too large')

        return parse_html(html, dict(source))

    def parse(self, source: Dict) -> AdapterResult:
        return AdapterResult(source, self.fetch(source))
