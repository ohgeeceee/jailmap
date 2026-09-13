#!/usr/bin/env python3
"""Research and catalog jail roster sources for a state.

For each county, finds the roster URL and detects the vendor type.
Outputs a CSV catalog and generates adapter stubs.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

VENDOR_FINGERPRINTS = {
    "tyler_newworld": [
        "InmateInquiry", "NewWorld", "tylerapp.com", "NewWorld.InmateInquiry",
        "TylerTechnologies", "tylertech.com"
    ],
    "zuercher": [
        "Zuercher", "zuerc", "portal.powerdms.com", "powerdms.com",
        "zuerchersoft", "zuerchertech.com"
    ],
    "crimegraphics_superdisplay": [
        "CrimeGraphics", "SuperDisplay", "omnify", "omnify.com",
        "CrimeGraphics.com", "SuperDisplay.com"
    ],
    "courtview": [
        "CourtView", "courtview.com", "Tyler Technologies",
        "TylerTechnologies", "tylertech.com/courtview"
    ],
    "ossi": [
        "OSSI", "ossiweb", "inmatelist", "ossiweb.com",
        "OSIsoft", "ossi.com"
    ],
    "smartweb": [
        "SmartWEB", "g-green-backend", "watchguard",
        "Google Cloud Storage", "storage.googleapis.com"
    ],
    "custom_html_table": [
        "<table", "inmate-roster", "current-inmates",
        "inmate_roster", "inmatelist", "booking_log"
    ],
    "wordpress": [
        "wp-content", "wp-json", "wordpress",
        "wp-includes", "generator\" content=\"WordPress"
    ],
}


def search_county_roster(state: str, county: str) -> Optional[str]:
    """Search for a county's roster URL. Returns URL or None."""
    import subprocess
    queries = [
        f'"{county} County {state} jail roster"',
        f'"{county} County {state} inmate search"',
        f'"{county} County {state} sheriff inmate roster"',
    ]
    for query in queries:
        try:
            result = subprocess.run(
                ["python3", "-c", f"""
import sys, json
sys.path.insert(0, "/app")
from hermes_tools import web_search
r = web_search(query={json.dumps(query)}, limit=3)
print(json.dumps(r.get("data", {{}}).get("web", [])))
"""],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                results = json.loads(result.stdout.strip())
                for item in results:
                    url = item.get("url", "")
                    if url and is_roster_url(url, state, county):
                        return url
        except Exception as e:
            pass
    return None


def is_roster_url(url: str, state: str, county: str) -> bool:
    """Check if a URL is likely a jail roster page."""
    url_lower = url.lower()
    if "facebook.com" in url or "twitter.com" in url or "youtube.com" in url:
        return False
    if ".pdf" in url_lower:
        return True
    roster_keywords = ["jail", "inmate", "roster", "detention", "sheriff", "booking"]
    if any(k in url_lower for k in roster_keywords):
        return True
    return False


def detect_vendor(html: str) -> str:
    """Detect roster vendor from HTML content."""
    html_lower = html.lower()
    for vendor, patterns in VENDOR_FINGERPRINTS.items():
        for pattern in patterns:
            if pattern.lower() in html_lower:
                return vendor
    return "unknown"


def fetch_roster_page(url: str) -> Optional[str]:
    """Fetch a roster page. Returns HTML or None on error."""
    try:
        with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
            response = client.get(url, headers=HEADERS)
            if response.status_code == 200:
                return response.text
    except Exception:
        pass
    return None


def research_state(state: str, output_csv: str) -> List[Dict]:
    """Research all counties in a state."""
    # Get counties from jurisdictions table or use hardcoded list
    counties = get_state_counties(state)
    print(f"Researching {len(counties)} counties in {state}...")
    
    results = []
    for i, county in enumerate(counties):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(counties)}")
        
        url = search_county_roster(state, county)
        if not url:
            results.append({
                "state": state, "county": county, "tier": get_tier(state, county),
                "facility": f"{county} County Jail", "source_type": "none",
                "source_url": "", "access_status": "no_public_source",
                "update_frequency": "daily", "notes": "No public roster found",
                "adapter_strategy": "none"
            })
            continue
        
        html = fetch_roster_page(url)
        if not html:
            results.append({
                "state": state, "county": county, "tier": get_tier(state, county),
                "facility": f"{county} County Jail", "source_type": "blocked",
                "source_url": url, "access_status": "blocked",
                "update_frequency": "daily", "notes": "Page blocked or unreachable",
                "adapter_strategy": "blocked"
            })
            continue
        
        vendor = detect_vendor(html)
        results.append({
            "state": state, "county": county, "tier": get_tier(state, county),
            "facility": f"{county} County Jail", "source_type": vendor,
            "source_url": url, "access_status": "active",
            "update_frequency": "daily", "notes": f"Detected vendor: {vendor}",
            "adapter_strategy": vendor
        })
        
        time.sleep(0.5)  # Be polite
    
    # Write CSV
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "state", "county", "tier", "facility", "source_type",
            "source_url", "access_status", "update_frequency", "notes",
            "adapter_strategy"
        ])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results written to {output_csv}")
    return results


def get_state_counties(state: str) -> List[str]:
    """Get counties for a state."""
    # From national-seed.sql or hardcode major ones
    COUNTIES = {
        "AL": ["Autauga", "Baldwin", "Barbour", "Bibb", "Blount", "Bullock", "Butler",
               "Calhoun", "Chambers", "Cherokee", "Chilton", "Choctaw", "Clarke", "Clay",
               "Cleburne", "Coffee", "Colbert", "Conecuh", "Coosa", "Covington", "Crenshaw",
               "Cullman", "Dale", "Dallas", "DeKalb", "Elmore", "Escambia", "Etowah",
               "Fayette", "Franklin", "Geneva", "Greene", "Hale", "Henry", "Houston",
               "Jackson", "Jefferson", "Lamar", "Lauderdale", "Lawrence", "Lee", "Limestone",
               "Lowndes", "Macon", "Madison", "Marengo", "Marion", "Marshall", "Mobile",
               "Monroe", "Montgomery", "Morgan", "Perry", "Pickens", "Pike", "Randolph",
               "Russell", "Shelby", "St. Clair", "Sumter", "Talladega", "Tallapoosa",
               "Tuscaloosa", "Walker", "Washington", "Wilcox", "Winston"],
        "AK": ["Anchorage", "Bethel", "Bristol Bay", "Dillingham", "Fairbanks North Star",
               "Haines", "Juneau", "Kenai Peninsula", "Ketchikan Gateway", "Kodiak Island",
               "Kusilvak", "Lake and Peninsula", "Matanuska-Susitna", "Nome", "North Slope",
               "Northwest Arctic", "Petersburg", "Prince of Wales-Hyder", "Sitka",
               "Skagway", "Southeast Fairbanks", "Wrangell", "Yakutat", "Yukon-Koyukuk"],
    }
    return COUNTIES.get(state, [f"{state} County"])


def get_tier(state: str, county: str) -> str:
    """Determine priority tier."""
    top_counties = {
        "Los Angeles", "Cook", "Harris", "Maricopa", "San Diego", "Orange",
        "Dallas", "Riverside", "Clark", "Kings", "Miami-Dade", "Broward",
        "Queens", "San Francisco", "Alameda", "Philadelphia", "Sacramento",
        "Hennepin", "Franklin", "Cuyahoga", "Allegheny", "Travis", "Bexar",
        "Tarrant", "Mecklenburg", "Wake", "Fulton", "DeKalb", "Cobb", "Gwinnett"
    }
    if county in top_counties:
        return "1"
    return "2"


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "AL"
    output = f"/root/jailmap/data/{state.lower()}-jail-sources.csv"
    research_state(state, output)
