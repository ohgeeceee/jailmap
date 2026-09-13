from __future__ import annotations

"""
Quick script to identify Montana jail roster sources.
Run: python3 /root/jailmap/scripts/discover_mt_rovers.py
"""

import requests
from pathlib import Path
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (jailmap/1.0; contact ops@jailmap.com)"}

MT_COUNTIES = [
    "Ada", "Amacus", "Boulder", "Cascade", "Chouteau", "Custer", "Daniels", "Dawson",
    "Deer Lodge", "Fallon", "Fergus", "Garden", "Garfield", "Glacier", "Golden Valley",
    "Granite", "Hill", "Jefferson", "Judith Basin", "Lewis and Clark", "Liberty",
    "Lincoln", "Madison", "McCone", "Meagher", "Mineral", "Missoula", "Musselshell",
    "Powder River", "Pondera", "Powell", "Ravalli", "Richland", "Roosevelt", "Rosebud",
    "Sanders", "Sheridan", "Silver Bow", "Stillwater", "Sweet Grass", "Teton",
    "Treasure", "Valley", "Wheatland", "Wibaux", "Yellowstone"
]


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("&", "and")


def test_url(name: str, url: str) -> dict:
    """Test a single URL and return status info."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = {
            "county": name,
            "url": url,
            "status": r.status_code,
            "has_table": "<table" in r.text.lower(),
            "has_roster": "inmate" in r.text.lower() or "roster" in r.text.lower(),
            "has_pdf": r.text.lower().endswith(".pdf") or "pdf" in r.text.lower(),
            "text_length": len(r.text),
            "error": None
        }
        # Check for common roster elements
        if "booking" in r.text.lower():
            data["has_booking"] = True
        if "charges" in r.text.lower() or "bond" in r.text.lower():
            data["has_details"] = True
        return data
    except Exception as e:
        return {
            "county": name,
            "url": url,
            "status": "ERROR",
            "error": str(e),
            "has_table": False,
            "has_roster": False
        }


def discover_mt_jails():
    """Discover jail roster sources for all Montana counties."""
    results = []

    # Common URL patterns by source type
    patterns = {
        "idaho.gov": "https://{slug}.idaho.gov/roster.php",
        "sheriff.com": "https://www.{slug}sheriff.com/inmate-roster",
        "county.mt.gov": "https://www.{slug}-county.mt.gov/jail-roster",
        "county.mt.gov/page": "https://www.{slug}-county.mt.gov/page/jail-roster",
        "county mtgov": "https://www.{slug}-county.mt.gov/jail",
        "mtgovsheriff": "https://{slug}-county.mt.gov/departments/sheriffs-office",
        "sheriff-jail": "https://www.{slug}sheriff.org/jail",
        "sheriff-roster": "https://www.{slug}sheriff.org/roster",
        "county sheriff": f"https://www.{slug}county.mt.gov/sheriff",
    }

    for county in MT_COUNTIES:
        slug = slugify(county)
        county_results = []

        for pattern_name, pattern_url in patterns.items():
            url = pattern_url.format(slug=slug, county=county.lower().replace(" ", "-"))
            result = test_url(county, url)
            result["pattern"] = pattern_name
            county_results.append(result)

            if result.get("has_table") or result.get("has_roster") or result.get("has_details"):
                break  # Found a working source

        results.append(county_results)

    return results


def main():
    print("Discovering Montana jail roster sources...\n")
    results = discover_mt_jails()

    for county_results in results:
        for r in county_results:
            if r.get("has_table") or r.get("has_roster") or r.get("has_details") or r.get("status") == "ERROR":
                status_str = f"[{r['status']}]"
                found = []
                if r.get("has_table"):
                    found.append("HTML table")
                if r.get("has_roster"):
                    found.append("roster page")
                if r.get("has_details"):
                    found.append("charges/bond")
                print(f"{r['county']}: {status_str} {', '.join(found)} - {r['url']}")
                if r.get("error"):
                    print(f"    ERROR: {r['error']}")
                break  # Only show first working source


if __name__ == "__main__":
    main()