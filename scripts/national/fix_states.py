#!/usr/bin/env python3
"""
Fix the 618 rows in census-follow.csv where state column has county names
(e.g. 'Calhoun County') instead of a 2-letter state code.

We infer state from the URL domain or the county name itself (since most
county names are unique enough when paired with state-specific .gov domains).
We use source-census.csv as a ground-truth reference for county→state mapping.
"""
import csv
import re
from pathlib import Path

# Build county→state map from source-census.csv (which has correct state codes)
county_to_state = {}
with open("data/national/source-census.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        state = (row.get("state") or "").strip().upper()
        county = (row.get("county") or "").strip().lower()
        if len(state) == 2 and county:
            county_to_state[county] = state

# Also from census-follow.csv's good rows
with open("data/national/census-follow.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        state = (row.get("state") or "").strip().upper()
        county = (row.get("county") or "").strip().lower()
        if len(state) == 2 and county:
            county_to_state[county] = state

# URL domain → state heuristics (specific patterns)
# Build a regex for well-known state domains
STATE_DOMAINS = {
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
    # hyphenated variants
    "west-virginia": "WV",
}
STATE_ABBRS = {
    "al": "AL", "ak": "AK", "az": "AZ", "ar": "AR", "ca": "CA", "co": "CO",
    "ct": "CT", "de": "DE", "fl": "FL", "ga": "GA", "hi": "HI", "id": "ID",
    "il": "IL", "in": "IN", "ia": "IA", "ks": "KS", "ky": "KY", "la": "LA",
    "me": "ME", "md": "MD", "ma": "MA", "mi": "MI", "mn": "MN", "ms": "MS",
    "mo": "MO", "mt": "MT", "ne": "NE", "nv": "NV", "nh": "NH", "nj": "NJ",
    "nm": "NM", "ny": "NY", "nc": "NC", "nd": "ND", "oh": "OH", "ok": "OK",
    "or": "OR", "pa": "PA", "ri": "RI", "sc": "SC", "sd": "SD", "tn": "TN",
    "tx": "TX", "ut": "UT", "vt": "VT", "va": "VA", "wa": "WA", "wv": "WV",
    "wi": "WI", "wy": "WY",
}


def infer_state(row):
    """Infer 2-letter state from county name or URL."""
    county = (row.get("county") or "").strip()
    county_lower = county.lower()
    # Direct county lookup
    if county_lower in county_to_state:
        return county_to_state[county_lower]
    # Without "county" suffix
    suffix_stripped = re.sub(r'\s+(county|parish|borough|census area)$', '', county_lower).strip()
    if suffix_stripped in county_to_state:
        return county_to_state[suffix_stripped]
    # From URL hints
    url = (row.get("candidate_url") or "").strip().lower()
    # state-specific .gov domains: e.g. "alabama.gov", "tx.us"
    for name, abbr in STATE_DOMAINS.items():
        if f".{name}." in url or url.startswith(f"{name}."):
            return abbr
    # State abbreviation in URL (e.g. ".al.gov", ".tx.us")
    m = re.search(r'\.([a-z]{2})\.(?:gov|us|org|com|net)/', f".{url}")
    if m and m.group(1) in STATE_ABBRS:
        return STATE_ABBRS[m.group(1)]
    return ""


def main():
    in_path = Path("data/national/census-follow.csv")
    out_path = Path("data/national/census-follow-fixed.csv")

    fixed = 0
    already_good = 0
    unfixed = 0
    seen = set()

    with in_path.open(encoding="utf-8-sig", newline="") as incsv, \
         out_path.open("w", newline="") as outcsv:
        reader = csv.DictReader(incsv)
        writer = csv.DictWriter(outcsv, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            state = (row.get("state") or "").strip()
            if len(state) != 2 or not state.isalpha() or not state.isupper():
                inferred = infer_state(row)
                if inferred:
                    row["state"] = inferred.upper()
                    fixed += 1
                else:
                    unfixed += 1
                    if unfixed <= 5:
                        print(f"UNFIXED: county={row.get('county')!r} url={row.get('candidate_url')!r}")
                    continue
            else:
                already_good += 1

            # dedupe
            key = (row.get("state"), row.get("county", "").strip().lower(), row.get("candidate_url", "").strip())
            if key in seen:
                continue
            seen.add(key)

            writer.writerow(row)

    print(f"\nalready_good: {already_good}, fixed: {fixed}, unfixed: {unfixed}")
    print(f"total written: {already_good + fixed}")


if __name__ == "__main__":
    main()
