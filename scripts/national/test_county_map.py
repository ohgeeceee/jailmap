#!/usr/bin/env python3
"""Build a comprehensive county→state map from all available data,
then re-run recovery with more coverage.
"""
import csv
import re
from pathlib import Path

# Known county→state for common/ambiguous counties not derivable from URL
COUNTY_STATE_OVERRIDES = {
    # format: "county_clean": "ST"
    # AL
    "calhoun": "AL", "franklin": "AL", "escambia": "AL", "jackson": "AL",
    "houston": "AL", "lauderdale": "AL", "limestone": "AL", "mobile": "AL",
    # AZ
    "gila": "AZ", "pinal": "AZ",
    # CA
    "napa": "CA", "placer": "CA", "san mateo": "CA", "san joaquin": "CA",
    # CO
    "alamosa": "CO", "archuleta": "CO",
    # FL
    "suwannee": "FL",
    # GA
    "bartow": "GA", "ben hill": "GA", "chatham": "GA", "gwinnett": "GA",
    "irwin": "GA",
    # IL
    "sangamon": "IL", "stephenson": "IL",
    # KS
    "cowley": "KS", "shawnee": "KS",
    # KY
    "graves": "KY",
}

county_to_state = {}

# Build from source-census.csv (correct state codes)
with open("data/national/source-census.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        state = (row.get("state") or "").strip().upper()
        county = (row.get("county") or "").strip().lower()
        county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
        if len(state) == 2 and county_clean:
            county_to_state[county_clean] = state

# Build from census-follow.csv good rows
with open("data/national/census-follow.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        state = (row.get("state") or "").strip().upper()
        county = (row.get("county") or "").strip().lower()
        county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
        if len(state) == 2 and county_clean:
            county_to_state[county_clean] = state

# Merge overrides (they take precedence for ambiguous cases)
county_to_state.update(COUNTY_STATE_OVERRIDES)

print(f"County map entries: {len(county_to_state)}")
# Check coverage of the 115 skipped rows
skipped_urls = [
    "gilacountyaz.gov", "pinal.gov", "napacounty.gov", "placerlafcoca.gov",
    "mysamcera.org", "sjsheriff.org", "alamosa.gov", "archuletacounty.gov",
    "suwanneecountyfl.gov", "bartowcountyga.gov", "benhillcounty-ga.gov",
    "sheriff.chathamcountyga.gov", "gwinnettcounty.com", "irwincounty-ga.gov",
    "sangamonil.gov", "stephensoncountyil.gov", "cowleycountyks.gov",
    "ares.sncoapps.us", "gravescountyky.gov",
]
for url in skipped_urls:
    print(f"  {url}")
