"""Alabama county jail roster adapters.

Each parse function takes a source dict with source_url, state, county, facility_name
and returns an AdapterResult with normalized records.
"""
from __future__ import annotations

from typing import Any, Dict

from backend.adapters.alabama import (
    fetch_html,
    AdapterResult,
    parse_html_table_roster,
    parse_jefferson_style_roster,
    parse_madison_style_roster,
)


def jefferson_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Jefferson County, AL - NewWorld/InmateInquiry portal or roster.php."""
    url = source.get("source_url", "https://www.jeffcoso.org/roster.php")
    try:
        html = fetch_html(url)
        records = parse_jefferson_style_roster(html, url, county="Jefferson", facility_name=source.get("facility_name", "Jefferson County Jail"))
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def mobile_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Mobile County, AL - Who's in Jail table roster."""
    url = source.get("source_url", "https://www.mobileso.com/whos-in-jail/")
    try:
        html = fetch_html(url)
        records = parse_html_table_roster(html, url, county="Mobile", facility_name=source.get("facility_name", "Mobile County Jail"))
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def madison_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Madison County, AL - SmartWEB roster with booking cards."""
    url = source.get("source_url", "https://www.madisoncountysheriffal.org/inmate-roster")
    try:
        html = fetch_html(url)
        records = parse_madison_style_roster(html, url, county="Madison", facility_name=source.get("facility_name", "Madison County Jail"))
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def montgomery_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Montgomery County, AL - uses same NewWorld portal as Jefferson."""
    url = source.get("source_url", "https://sheriff.montgomeryal.gov/NewWorld.InmateInquiry/")
    try:
        html = fetch_html(url)
        records = parse_jefferson_style_roster(html, url, county="Montgomery", facility_name=source.get("facility_name", "Montgomery County Jail"))
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def tuscaloosa_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Tuscaloosa County, AL."""
    url = source.get("source_url", "https://www.tuscaloosasheriff.com/inmate-roster")
    try:
        html = fetch_html(url)
        # Try table format first, fall back to div format
        records = parse_html_table_roster(html, url, county="Tuscaloosa", facility_name=source.get("facility_name", "Tuscaloosa County Jail"))
        if not records:
            records = parse_jefferson_style_roster(html, url, county="Tuscaloosa", facility_name=source.get("facility_name", "Tuscaloosa County Jail"))
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


def baldwin_county_al(source: Dict[str, Any]) -> AdapterResult:
    """Baldwin County, AL."""
    url = source.get("source_url", "https://baldwincountysheriff.org/inmate-roster/")
    try:
        html = fetch_html(url)
        records = parse_html_table_roster(html, url, county="Baldwin", facility_name=source.get("facility_name", "Baldwin County Jail"))
        if not records:
            records = parse_jefferson_style_roster(html, url, county="Baldwin", facility_name=source.get("facility_name", "Baldwin County Jail"))
        return AdapterResult(source, records)
    except Exception as e:
        return AdapterResult(source, [])


ALABAMA_ADAPTERS = {
    "jefferson_county_al": jefferson_county_al,
    "mobile_county_al": mobile_county_al,
    "madison_county_al": madison_county_al,
    "montgomery_county_al": montgomery_county_al,
    "tuscaloosa_county_al": tuscaloosa_county_al,
    "baldwin_county_al": baldwin_county_al,
}
