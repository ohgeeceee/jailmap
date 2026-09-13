#!/usr/bin/env python3
"""Research catalog builder for all US county jail rosters.

For each county, searches for roster URL, detects vendor type, and writes to CSV.
No subagent delegation needed — uses web_search directly.

Usage:
    python3 scripts/build_research_catalog.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# All US counties by state (top 100 most populous counties)
# Source: US Census Bureau
TOP_COUNTIES = {
    "AL": ["Jefferson", "Mobile", "Madison", "Montgomery", "Baldwin", "Tuscaloosa", "Shelby", "Elmore", "Houston", "Lee"],
    "AZ": ["Maricopa", "Pima", "Yavapai", "Yuma", "Mohave", "Coconino", "Navajo", "Apache", "Gila", "Pinal"],
    "CA": ["Los Angeles", "San Diego", "Orange", "Riverside", "San Bernardino", "Santa Clara", "Alameda", "Sacramento", "Contra Costa", "Fresno"],
    "CO": ["El Paso", "Denver", "Arapahoe", "Jefferson", "Adams", "Larimer", "Boulder", "Weld", "Douglas", "Pueblo"],
    "CT": ["Fairfield", "Hartford", "New Haven", "Litchfield", "Middlesex", "New London", "Tolland", "Windham"],
    "FL": ["Miami-Dade", "Broward", "Palm Beach", "Hillsborough", "Orange", "Pinellas", "Duval", "Lee", "Polk", "Brevard"],
    "GA": ["Fulton", "DeKalb", "Cobb", "Gwinnett", "Chatham", "Clayton", "Cherokee", "Henry", "Richmond", "Hall"],
    "IL": ["Cook", "DuPage", "Lake", "Will", "Kane", "McHenry", "Winnebago", "Madison", "St. Clair", "Champaign"],
    "IN": ["Marion", "Lake", "Allen", "Hamilton", "St. Joseph", "Elkhart", "Tippecanoe", "Vanderburgh", "Porter", "Hendricks"],
    "IA": ["Polk", "Linn", "Scott", "Johnson", "Black Hawk", "Woodbury", "Dubuque", "Story", "Dallas", "Pottawattamie"],
    "KS": ["Johnson", "Sedgwick", "Shawnee", "Wyandotte", "Douglas", "Leavenworth", "Riley", "Butler", "Reno", "Saline"],
    "KY": ["Jefferson", "Fayette", "Kenton", "Boone", "Warren", "Hardin", "Campbell", "Madison", "Bullitt", "Christian"],
    "LA": ["East Baton Rouge", "Jefferson", "Orleans", "St. Tammany", "Caddo", "Calcasieu", "Lafayette", "Ouachita", "Tangipahoa", "Livingston"],
    "MD": ["Montgomery", "Prince George's", "Baltimore", "Anne Arundel", "Howard", "Harford", "Carroll", "Frederick", "Charles", "Calvert"],
    "MI": ["Wayne", "Oakland", "Macomb", "Kent", "Genesee", "Washtenaw", "Ingham", "Ottawa", "Kalamazoo", "Saginaw"],
    "MN": ["Hennepin", "Ramsey", "Dakota", "Anoka", "Washington", "St. Louis", "Olmsted", "Scott", "Wright", "Crow Wing"],
    "MO": ["St. Louis", "Jackson", "St. Charles", "St. Louis City", "Greene", "Clay", "Jefferson", "Boone", "Jasper", "Cass"],
    "NC": ["Mecklenburg", "Wake", "Guilford", "Forsyth", "Cumberland", "Durham", "Buncombe", "Union", "Gaston", "Cabarrus"],
    "NE": ["Douglas", "Lancaster", "Sarpy", "Hall", "Buffalo", "Dodge", "Madison", "Lincoln", "Platte", "Adams"],
    "NJ": ["Bergen", "Middlesex", "Essex", "Hudson", "Ocean", "Monmouth", "Passaic", "Union", "Camden", "Morris"],
    "NM": ["Bernalillo", "Dona Ana", "Santa Fe", "Sandoval", "San Juan", "Valencia", "McKinley", "Lea", "Otero", "Chaves"],
    "NY": ["Kings", "Queens", "New York", "Suffolk", "Bronx", "Nassau", "Westchester", "Erie", "Monroe", "Richmond"],
    "OH": ["Cuyahoga", "Franklin", "Hamilton", "Summit", "Montgomery", "Lucas", "Stark", "Butler", "Lorain", "Mahoning"],
    "OK": ["Oklahoma", "Tulsa", "Cleveland", "Canadian", "Comanche", "Osage", "McClain", "Garfield", "Rogers", "Creek"],
    "OR": ["Multnomah", "Washington", "Clackamas", "Lane", "Marion", "Jackson", "Deschutes", "Linn", "Yamhill", "Benton"],
    "PA": ["Philadelphia", "Allegheny", "Montgomery", "Bucks", "Delaware", "Lancaster", "Chester", "Berks", "Lehigh", "Luzerne"],
    "SC": ["Greenville", "Richland", "Charleston", "Horry", "Spartanburg", "Lexington", "York", "Berkeley", "Florence", "Beaufort"],
    "TN": ["Shelby", "Davidson", "Knox", "Hamilton", "Rutherford", "Montgomery", "Williamson", "Sumner", "Sevier", "Blount"],
    "TX": ["Harris", "Dallas", "Tarrant", "Bexar", "Travis", "Collin", "Denton", "Fort Bend", "Hidalgo", "El Paso"],
    "UT": ["Salt Lake", "Utah", "Davis", "Weber", "Washington", "Cache", "Tooele", "Box Elder", "Iron", "Summit"],
    "VA": ["Fairfax", "Prince William", "Virginia Beach City", "Loudoun", "Chesterfield", "Henrico", "Norfolk City", "Richmond City", "Newport News City", "Arlington"],
    "WA": ["King", "Pierce", "Snohomish", "Spokane", "Clark", "Thurston", "Kitsap", "Yakima", "Whatcom", "Benton"],
    "WI": ["Milwaukee", "Dane", "Waukesha", "Racine", "Kenosha", "Brown", "Outagamie", "Winnebago", "Rock", "Washington"],
    "NV": ["Clark", "Washoe", "Carson City", "Douglas", "Lyon", "Elko", "Nye", "Humboldt", "Churchill", "Lander"],
    "NM": ["Bernalillo", "Dona Ana", "Santa Fe", "Sandoval", "San Juan", "Valencia", "McKinley", "Lea", "Otero", "Chaves"],
}


def search_roster_url(state: str, county: str) -> dict | None:
    """Search for a county's roster URL using web_search."""
    from hermes_tools import web_search
    
    queries = [
        f'"{county} County {state} jail roster"',
        f'"{county} County {state} inmate search"',
        f'"{county} {state} sheriff inmate roster"',
        f'site:{county.lower()}{state.lower()}.gov inmate roster',
    ]
    
    for query in queries:
        try:
            result = web_search(query=query, limit=5)
            items = result.get("data", {}).get("web", [])
            for item in items:
                url = item.get("url", "")
                desc = item.get("description", "")
                if url and is_roster_url(url, state, county):
                    vendor = detect_vendor(url, desc)
                    return {
                        "url": url,
                        "vendor": vendor,
                        "access_status": "active",
                        "notes": desc[:200],
                    }
        except Exception as e:
            continue
    
    return None


def is_roster_url(url: str, state: str, county: str) -> bool:
    """Check if a URL is likely a jail roster page."""
    url_lower = url.lower()
    # Exclude social media, news, and irrelevant sites
    if any(s in url_lower for s in ["facebook.com", "twitter.com", "youtube.com", "reddit.com", "instagram.com"]):
        return False
    # Must be HTTPS or HTTP
    if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
        return False
    # Look for roster-related keywords
    roster_keywords = ["jail", "inmate", "roster", "detention", "sheriff", "booking", "corrections", "custody"]
    if any(k in url_lower for k in roster_keywords):
        return True
    # Check if it's a PDF roster
    if ".pdf" in url_lower and any(k in url_lower for k in ["inmate", "roster", "jail", "booking"]):
        return True
    return False


def detect_vendor(url: str, description: str) -> str:
    """Detect roster vendor from URL and description."""
    combined = (url + " " + description).lower()
    
    if "tyler" in combined or "newworld" in combined or "tylerapp" in combined:
        return "tyler_newworld"
    if "zuercher" in combined or "powerdms" in combined:
        return "zuercher"
    if "crimegraphics" in combined or "superdisplay" in combined or "omnify" in combined:
        return "crimegraphics"
    if "courtview" in combined:
        return "courtview"
    if "ossi" in combined or "ossiweb" in combined:
        return "ossi"
    if ".pdf" in combined:
        return "pdf"
    if "smartweb" in combined or "g-green" in combined or "googleapis" in combined:
        return "smartweb"
    return "unknown"


def build_catalog(state: str) -> list[dict]:
    """Build research catalog for a state's top counties."""
    counties = TOP_COUNTIES.get(state, [])
    print(f"\n=== Building catalog for {state} ({len(counties)} counties) ===")
    
    catalog = []
    for i, county in enumerate(counties):
        print(f"  [{i+1}/{len(counties)}] {county} County, {state}...", end=" ", flush=True)
        
        result = search_roster_url(state, county)
        if result:
            catalog.append({
                "state": state,
                "county": county,
                "facility": f"{county} County Jail",
                "source_url": result["url"],
                "source_type": result["vendor"],
                "access_status": result["access_status"],
                "notes": result["notes"],
            })
            print(f"FOUND ({result['vendor']})")
        else:
            catalog.append({
                "state": state,
                "county": county,
                "facility": f"{county} County Jail",
                "source_url": "",
                "source_type": "none",
                "access_status": "no_public_source",
                "notes": "",
            })
            print("NO SOURCE")
        
        time.sleep(1)  # Rate limit
    
    # Write CSV
    output_path = Path(f"/root/jailmap/data/{state.lower()}-research-catalog.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "state", "county", "facility", "source_url", "source_type",
            "access_status", "notes",
        ])
        writer.writeheader()
        writer.writerows(catalog)
    
    found = sum(1 for r in catalog if r["source_url"])
    print(f"  Written to {output_path}: {found}/{len(counties)} with sources")
    return catalog


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", help="Single state to research")
    parser.add_argument("--all", action="store_true", help="Research all states")
    args = parser.parse_args()
    
    if args.state:
        build_catalog(args.state.upper())
    elif args.all:
        all_states = list(TOP_COUNTIES.keys())
        for state in all_states:
            build_catalog(state)
        print(f"\n=== COMPLETE: Catalogs for {len(all_states)} states ===")
    else:
        parser.print_help()
