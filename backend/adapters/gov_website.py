"""GovernmentWebsite.com vendor roster adapter.

The same vendor powers dozens of sheriff sites across multiple states. They all
share the same HTML structure:

    <div class="roster_name">FULL NAME</div>
    <div>
        <div class="inmate_data_bold"><strong>Booking #: </strong></div>
        <div class="inmate_data_content">BOOKING_NUMBER</div>
    </div>
    <div>
        <div class="inmate_data_bold"><strong>Age: </strong></div>
        <div class="inmate_data_content">AGE</div>
    </div>
    <div>
        <div class="inmate_data_bold"><strong>Booking Date: </strong></div>
        <div class="inmate_data_content">MM-DD-YYYY H:MM AM/PM</div>
    </div>
    <div>
        <div class="inmate_data_bold"><strong>Charges: </strong></div>
        <div class="inmate_data_content">CHARGE TEXT<br>...</div>
    </div>

Pagination is via standard links: /inmate-roster/filters/current/booking_time=desc/N

This adapter is staging-only — it returns rows for records.staged_bookings,
never directly into the public index.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List, Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from backend.adapters.idaho import AdapterResult, _assert_authorized, _fetch_html

MAX_PAGES = 50
MAX_ROWS = 2000
SOURCE_TIMEZONES = {"AR": ZoneInfo("America/Chicago")}


def _clean(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", unescape(str(value))).strip()


def _parse_date(value: str, state: str) -> Optional[str]:
    """Parse MM-DD-YYYY H:MM AM/PM format."""
    text = _clean(value)
    if not text:
        return None
    # Try the GovernmentWebsite format: 09-19-2026 5:30 PM
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)", text, re.IGNORECASE)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hour, minute = int(m.group(4)), int(m.group(5))
        ampm = m.group(6).upper()
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
        try:
            source_timezone = SOURCE_TIMEZONES.get(state)
            if source_timezone is None:
                raise ValueError(f"GovernmentWebsite timezone is not configured for {state}")
            dt = datetime(year, month, day, hour, minute, tzinfo=source_timezone)
            return dt.isoformat()
        except ValueError:
            return None
    return None


def _extract_field(block_html: str, label: str) -> str:
    """Extract the value for a given label from a roster block."""
    pattern = rf'<div class="inmate_data_bold"><strong>\s*{re.escape(label)}\s*:\s*</strong></div>\s*<div class="inmate_data_content">\s*(.*?)\s*</div>'
    m = re.search(pattern, block_html, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    value = m.group(1)
    # Remove <br> tags and extra whitespace
    value = re.sub(r"<br\s*/?>", " | ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)  # strip any remaining HTML
    return _clean(value)


def _parse_roster_page(html: str, source: Dict) -> List[Dict]:
    """Parse all roster entries from a single page of GovernmentWebsite HTML."""
    pulled_at = datetime.now(timezone.utc).isoformat()
    records = []

    # Split into individual roster blocks
    # Each block starts with <div class="roster_name">
    blocks = re.split(r'(?=<div class="roster_name">)', html)

    for block in blocks:
        name_match = re.search(r'<div class="roster_name">\s*(.*?)\s*</div>', block, re.DOTALL)
        if not name_match:
            continue

        full_name = _clean(name_match.group(1))
        if not full_name:
            continue

        booking_number = _extract_field(block, "Booking #")
        age_str = _extract_field(block, "Age")
        booking_date_str = _extract_field(block, "Booking Date")
        charges_str = _extract_field(block, "Charges")

        # Parse name
        first_name, last_name = "", full_name
        if "," in full_name:
            parts = full_name.split(",", 1)
            last_name = _clean(parts[0])
            first_name = _clean(parts[1]).split(" ")[0]
        else:
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])

        # Parse age
        if not age_str.isdigit():
            raise ValueError("Roster row is missing a parseable adult-eligibility age")
        age = int(age_str)
        if age < 18:
            continue

        # Parse booking date
        booking_date = _parse_date(booking_date_str, str(source.get("state", "")))
        if not booking_number or booking_date is None:
            raise ValueError("Roster row is missing a stable booking number or valid booking date")

        # Parse charges
        charges = []
        if charges_str:
            for charge_text in charges_str.split("|"):
                charge_text = _clean(charge_text)
                if charge_text:
                    charges.append({
                        "source_id": f"c{len(charges) + 1}",
                        "description": charge_text[:2000],
                        "statute": None,
                        "severity": None,
                    })

        # Mugshots are excluded unless a source-specific review explicitly approves them.
        mugshot_url = None

        # Extract profile link for detail page
        profile_match = re.search(r'href="(/inmate-roster/[a-f0-9]+)"', block)
        profile_url = urljoin(source["source_url"], profile_match.group(1)) if profile_match else None

        records.append({
            "state": source.get("state", ""),
            "county": source.get("county", ""),
            "facility": source.get("facility_name", ""),
            "source_url": source.get("source_url", ""),
            "source_type": "gov_website_roster",
            "pulled_at": pulled_at,
            "inmate_id": None,
            "booking_number": booking_number or None,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "dob": None,
            "age": age,
            "sex": None,
            "race": None,
            "booking_date": booking_date,
            "source_updated_at": booking_date,
            "status": "in_custody",
            "charges": charges,
            "bonds": [],
            "release_date": None,
            "mugshot_url": mugshot_url,
            "notes": f"Profile: {profile_url}" if profile_url else None,
        })

    return records


def _get_page_urls(base_html: str, source_url: str) -> List[str]:
    """Extract pagination URLs from the page."""
    urls = [source_url]  # First page is the source URL itself

    # Find pagination links
    page_links = re.findall(r'href="([^"]+/(\d+))"', base_html)
    seen = set()
    for link, page_num in page_links:
        page_num = int(page_num)
        if page_num <= 1 or page_num > MAX_PAGES:
            continue
        full_url = urljoin(source_url, link)
        if full_url not in seen:
            seen.add(full_url)
            urls.append(full_url)

    return urls[:MAX_PAGES]


def fetch(source) -> List[Dict]:
    """Fetch and parse GovernmentWebsite roster across all pages."""
    _assert_authorized(source["source_url"])

    # Fetch and parse page one once. Every advertised later page is required;
    # a partial current-custody snapshot must never be accepted as complete.
    first_page_html = _fetch_html(source["source_url"]).decode("utf-8", errors="ignore")
    page_urls = _get_page_urls(first_page_html, source["source_url"])

    all_records = _parse_roster_page(first_page_html, source)
    for page_url in page_urls[1:]:
        if len(all_records) >= MAX_ROWS:
            raise ValueError("Roster exceeds the configured row limit")
        html = _fetch_html(page_url).decode("utf-8", errors="ignore")
        all_records.extend(_parse_roster_page(html, source))

    if len(all_records) > MAX_ROWS:
        raise ValueError("Roster exceeds the configured row limit")
    booking_numbers = [row["booking_number"] for row in all_records]
    if len(booking_numbers) != len(set(booking_numbers)):
        raise ValueError("Duplicate booking numbers in complete roster snapshot")

    return all_records


def parse(source) -> AdapterResult:
    return AdapterResult(source, fetch(source))
