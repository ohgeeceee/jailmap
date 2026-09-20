#!/usr/bin/env python3
"""Fix state codes in existing leads file + rebuild final output."""
import csv
import re
from pathlib import Path

STATE_ABBRS = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}

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

ADDITIONAL_OVERRIDES = {
    "calhoun": "AL", "franklin": "AL", "escambia": "AL", "jackson": "AL",
    "houston": "AL", "lauderdale": "AL", "limestone": "AL", "mobile": "AL",
    "montgomery": "AL", "pinal": "AZ", "napa": "CA", "placer": "CA",
    "san mateo": "CA", "san joaquin": "CA", "alamosa": "CO", "archuleta": "CO",
    "gwinnett": "GA", "hawaii": "HI", "sangamon": "IL", "shawnee": "KS",
    "st mary": "LA", "gratiot": "MI", "hillsdale": "MI", "schoolcraft": "MI",
    "big stone": "MN", "hennepin": "MN", "koochiching": "MN", "rice": "MN",
    "cleburne": "AR", "conway": "AR", "poinsett": "AR", "mohave": "AZ",
    "butte": "CA", "calaveras": "CA", "lassen": "CA", "marin": "CA",
    "mariposa": "CA", "orange": "CA", "santa cruz": "CA", "sierra": "CA",
    "siskiyou": "CA", "tehama": "CA", "yuba": "CA", "bent": "CO",
    "boulder": "CO", "fremont": "CO", "summit": "CO", "teller": "CO",
    "weld": "CO", "kent": "DE", "flagler": "FL", "hardee": "FL",
    "manatee": "FL", "leon": "FL", "bartow": "GA", "ben hill": "GA",
    "chatham": "GA", "irwin": "GA", "cowley": "KS", "stephenson": "IL",
    "graves": "KY", "suwannee": "FL", "st mary": "LA",
    "texas": "MO", "flathead": "MT", "missoula": "MT",
    "durham": "NC", "cavalier": "ND", "stutsman": "ND",
    "sarpy": "NE", "seward": "NE", "grafton": "NH",
    "salem": "NJ", "lea": "NM", "los alamos": "NM", "santa fe": "NM",
    "washoe": "NV", "columbiana": "OH", "clackamas": "OR",
    "josephine": "OR", "tillamook": "OR", "elk": "PA", "montour": "PA",
    "newberry": "SC", "angelina": "TX", "nolan": "TX", "upshur": "TX",
    "utah": "UT", "addison": "VT", "pend oreille": "WA", "walla walla": "WA",
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

def infer_state(county, url):
    county_lower = county.lower()
    county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county_lower).strip()
    
    state = extract_state_from_url(url)
    if state:
        return state
    if county_clean in COUNTY_STATE_MAP:
        return COUNTY_STATE_MAP[county_clean]
    if county_clean in ADDITIONAL_OVERRIDES:
        return ADDITIONAL_OVERRIDES[county_clean]
    return ""

def main():
    build_county_map()
    COUNTY_STATE_MAP.update(ADDITIONAL_OVERRIDES)
    
    # Read existing leads file
    in_path = Path("data/national/official-jail-source-leads.csv")
    out_path = Path("data/national/official-jail-source-leads-fixed.csv")
    
    fixed = 0
    already_good = 0
    unfixed = 0
    
    with in_path.open(encoding="utf-8-sig", newline="") as incsv, \
         out_path.open("w", newline="") as outcsv:
        reader = csv.DictReader(incsv)
        writer = csv.DictWriter(outcsv, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            state = (row.get("state") or "").strip()
            is_bad = len(state) != 2 or not state.isalpha() or not state.isupper()
            
            if is_bad:
                county = (row.get("county") or "").strip()
                url = (row.get("source_url") or "").strip()
                inferred = infer_state(county, url)
                if inferred:
                    row["state"] = inferred.upper()
                    fixed += 1
                else:
                    unfixed += 1
                    if unfixed <= 20:
                        print(f"UNFIXED: county={county!r} url={url!r}")
                    # Still write the row (just in case)
            else:
                already_good += 1
            
            writer.writerow(row)
    
    print(f"\nalready_good: {already_good}, fixed: {fixed}, unfixed: {unfixed}")

if __name__ == "__main__":
    main()
