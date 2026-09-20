#!/usr/bin/env python3
"""
Recover state codes for the 617 rows in census-follow.csv where the state
column contains county names instead of 2-letter codes.

Strategy (in priority order):
1. county→state lookup from the 1558 correctly-coded rows
2. URL contains a state name (e.g. "alabama") or abbreviation (e.g. "al")
3. Skip rows where state is ambiguous (e.g. Calhoun County exists in 8 states)
"""
import csv
import re
from pathlib import Path

county_to_state = {}
with open("data/national/source-census.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        state = (row.get("state") or "").strip().upper()
        county = (row.get("county") or "").strip().lower()
        county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
        if len(state) == 2 and county_clean:
            county_to_state[county_clean] = state

with open("data/national/census-follow.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        state = (row.get("state") or "").strip().upper()
        county = (row.get("county") or "").strip().lower()
        county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
        if len(state) == 2 and county_clean:
            county_to_state[county_clean] = state

STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "newhampshire": "NH", "newjersey": "NJ",
    "newmexico": "NM", "newyork": "NY", "northcarolina": "NC",
    "northdakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhodeisland": "RI", "southcarolina": "SC",
    "southdakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "westvirginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "districtofcolumbia": "DC",
}

# state abbreviations that appear in URLs like "al", "tx", "ca"
STATE_ABBRS = set(v for v in STATE_NAMES.values())

# County names that are unique enough to infer state from domain patterns
# calcoso.org = Calhoun County, AL
COUNTY_DOMAINS = {
    "calcoso.org": "AL",
    "franklinalabama.gov": "AL",
    "escambiacountysheriffal.gov": "AL",
    "jacksoncountyal.gov": "AL",
    "houstoncosoal.gov": "AL",
    "lauderdalesheriff.org": "AL",  # Lauderdale County, AL
    "limestonecounty-al.gov": "AL",
    "mobileccc.gov": "AL",
    "montgomerycountyal.gov": "AL",
    "randolphcountyal.gov": "AL",
    "winstonal.gov": "AL",
    "carrollcountysheriffar.gov": "AR",
    "cleburnearso.gov": "AR",
    "clarkcountyar.gov": "AR",
    "conwayarkansas.gov": "AR",
    "greenesoar.gov": "AR",
    "hotspringcountysoar.gov": "AR",
    "poinsettar.gov": "AR",
    "sebastiancountyar.gov": "AR",
}


def infer_state(row):
    county = (row.get("county") or "").strip()
    county_lower = county.lower()
    county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county_lower).strip()
    url = (row.get("candidate_url") or "").strip().lower()

    # 1. Direct county lookup (if unique)
    if county_clean in county_to_state:
        return county_to_state[county_clean]

    # 2. URL exact domain match
    for domain, abbr in COUNTY_DOMAINS.items():
        if url.endswith(domain) or url == domain:
            return abbr

    # 3. URL contains state name
    for name, abbr in STATE_NAMES.items():
        if name in url:
            return abbr

    # 4. URL contains state abbreviation as a component (e.g. ".al.gov", "county-al")
    # Split URL by dots/dashes/slashes and look for state abbreviations
    url_parts = re.split(r'[.\-/]', url)
    for part in url_parts:
        if part in STATE_ABBRS:
            return part.upper()

    return ""


def main():
    in_path = Path("data/national/census-follow.csv")
    out_path = Path("data/national/census-follow-recovered.csv")

    fixed = 0
    skipped = 0
    seen = set()

    with in_path.open(encoding="utf-8-sig", newline="") as incsv, \
         out_path.open("w", newline="") as outcsv:
        reader = csv.DictReader(incsv)
        writer = csv.DictWriter(outcsv, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            state = (row.get("state") or "").strip()
            is_bad = len(state) != 2 or not state.isalpha() or not state.isupper()

            if is_bad:
                inferred = infer_state(row)
                if inferred:
                    row["state"] = inferred.upper()
                    fixed += 1
                else:
                    skipped += 1
                    if skipped <= 20:
                        print(f"SKIP: county={row.get('county')!r} url={row.get('candidate_url')!r}")
                    continue

            # dedupe
            key = (row.get("state"), row.get("county", "").strip().lower(), row.get("candidate_url", "").strip())
            if key in seen:
                continue
            seen.add(key)

            writer.writerow(row)

    print(f"\nfixed: {fixed}, skipped: {skipped}")
    print(f"total written to recovered file: {fixed + (len(seen) - fixed)}")


if __name__ == "__main__":
    main()
