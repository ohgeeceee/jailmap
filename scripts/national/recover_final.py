#!/usr/bin/env python3
"""Add the 52 remaining skip counties and re-run recovery."""
import csv
import re
from pathlib import Path

COUNTY_STATE_MAP = {}

def build_county_map():
    with open("data/national/source-census.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip().lower()
            county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
            if len(state) == 2 and county_clean:
                COUNTY_STATE_MAP[county_clean] = state
    with open("data/national/census-follow.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip().lower()
            county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
            if len(state) == 2 and county_clean:
                COUNTY_STATE_MAP[county_clean] = state

# Additional overrides for the 52 skipped counties
ADDITIONAL_OVERRIDES = {
    "pinal": "AZ",
    "napa": "CA",
    "placer": "CA",
    "san mateo": "CA",
    "san joaquin": "CA",
    "alamosa": "CO",
    "archuleta": "CO",
    "gwinnett": "GA",
    "hawaii": "HI",
    "sangamon": "IL",
    "shawnee": "KS",
    "st mary": "LA",
    "gratiot": "MI",
    "hillsdale": "MI",
    "schoolcraft": "MI",
    "big stone": "MN",
    "hennepin": "MN",
    "koochiching": "MN",
    "rice": "MN",
    # From the URL-based detection
    "autauga": "AL",
    "baldwin": "AL",
    "barbour": "AL",
    "bibb": "AL",
    "blount": "AL",
    "bullock": "AL",
    "butler": "AL",
    "calhoun": "AL",
    "chambers": "AL",
    "cherokee": "AL",
    "chilton": "AL",
    "choctaw": "AL",
    "clarke": "AL",
    "clay": "AL",
    "cleburne": "AL",
    "coffee": "AL",
    "colbert": "AL",
    "conecuh": "AL",
    "coosa": "AL",
    "covington": "AL",
    "crenshaw": "AL",
    "cullman": "AL",
    "dale": "AL",
    "dallas": "AL",
    "dekalb": "AL",
    "elmore": "AL",
    "escambia": "AL",
    "etowah": "AL",
    "fayette": "AL",
    "franklin": "AL",
    "geneva": "AL",
    "greene": "AL",
    "hale": "AL",
    "henry": "AL",
    "houston": "AL",
    "jackson": "AL",
    "jefferson": "AL",
    "lamar": "AL",
    "lauderdale": "AL",
    "lawrence": "AL",
    "lee": "AL",
    "limestone": "AL",
    "lowndes": "AL",
    "macon": "AL",
    "madison": "AL",
    "marengo": "AL",
    "marion": "AL",
    "marshall": "AL",
    "mobile": "AL",
    "monroe": "AL",
    "montgomery": "AL",
    "morgan": "AL",
    "perry": "AL",
    "pickens": "AL",
    "pike": "AL",
    "randolph": "AL",
    "russell": "AL",
    "shelby": "AL",
    "st clair": "AL",
    "sumter": "AL",
    "talladega": "AL",
    "tallapoosa": "AL",
    "tuscaloosa": "AL",
    "walker": "AL",
    "washington": "AL",
    "wilcox": "AL",
    "winston": "AL",
    "cleburne": "AR",
    "conway": "AR",
    "poinsett": "AR",
    "mohave": "AZ",
    "butte": "CA",
    "calaveras": "CA",
    "lassen": "CA",
    "marin": "CA",
    "mariposa": "CA",
    "orange": "CA",
    "santa cruz": "CA",
    "sierra": "CA",
    "siskiyou": "CA",
    "tehama": "CA",
    "yuba": "CA",
    "bent": "CO",
    "boulder": "CO",
    "fremont": "CO",
    "summit": "CO",
    "teller": "CO",
    "weld": "CO",
    "kent": "DE",
    "flagler": "FL",
    "hardee": "FL",
    "manatee": "FL",
    "leon": "FL",
    "bartow": "GA",
    "ben hill": "GA",
    "chatham": "GA",
    "gwinnett": "GA",
    "irwin": "GA",
    "cowley": "KS",
    "shawnee": "KS",
    "st mary": "LA",
    "sangamon": "IL",
    "stephenson": "IL",
    "gratiot": "MI",
    "hillsdale": "MI",
    "schoolcraft": "MI",
    "big stone": "MN",
    "hennepin": "MN",
    "koochiching": "MN",
    "rice": "MN",
    "graves": "KY",
    "suwannee": "FL",
}

def main():
    build_county_map()
    COUNTY_STATE_MAP.update(ADDITIONAL_OVERRIDES)
    print(f"County map entries: {len(COUNTY_STATE_MAP)}")

    in_path = Path("data/national/census-follow.csv")
    out_path = Path("data/national/census-follow-final.csv")

    fixed = 0
    skipped = 0
    seen = set()
    total_written = 0

    STATE_ABBRS = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
        "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
        "VA","WA","WV","WI","WY","DC",
    }

    def extract_state_from_url(url):
        url_lower = url.lower()
        patterns = [
            r'county([a-z]{2})(?:\.gov|\.us|\.org|\.com|/)',
            r'county-([a-z]{2})(?:\.gov|\.us|\.org|\.com|/)',
            r'county_([a-z]{2})(?:\.gov|\.us|\.org|\.com|/)',
            r'\.([a-z]{2})(?:\.gov|\.us|\.org)',
            r'\.([a-z]{2})(?:\.gov|\.us|\.org|\.com)/',
        ]
        for pattern in patterns:
            m = re.search(pattern, url_lower)
            if m and m.group(1).upper() in STATE_ABBRS:
                return m.group(1).upper()
        return ""

    def infer_state(row):
        county = (row.get("county") or "").strip().lower()
        county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
        url = (row.get("candidate_url") or "").strip()

        state = extract_state_from_url(url)
        if state:
            return state
        if county_clean in COUNTY_STATE_MAP:
            return COUNTY_STATE_MAP[county_clean]
        return ""

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
                    if skipped <= 30:
                        print(f"SKIP: county={row.get('county')!r} url={row.get('candidate_url')!r}")
                    continue

            key = (row.get("state"), row.get("county", "").strip().lower(), row.get("candidate_url", "").strip())
            if key in seen:
                continue
            seen.add(key)

            writer.writerow(row)
            total_written += 1

    print(f"\nfixed: {fixed}, skipped: {skipped}")
    print(f"total written: {total_written}")


if __name__ == "__main__":
    main()
