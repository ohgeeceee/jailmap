from __future__ import annotations

import re
import csv
import requests
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path("/root/jailmap/states")
STATE_TABLES = {
    "MT": "https://en.wikipedia.org/wiki/List_of_counties_in_Montana",
    "ID": "https://en.wikipedia.org/wiki/List_of_counties_in_Idaho",
    "SD": "https://en.wikipedia.org/wiki/List_of_counties_in_South_Dakota",
}


def _slugify(name: str) -> str:
    cleaned = re.sub(r"\bcounty\b", "", name, flags=re.IGNORECASE).strip()
    return "-".join(cleaned.lower().split())


def _fetch_counties(state: str, url: str) -> list[str]:
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find_all("table", class_="wikitable")[0]
    names = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all(["td", "th"])
        if not tds:
            continue
        a = tds[0].find("a")
        name = a.get_text(strip=True) if a else tds[0].get_text(strip=True)
        if name:
            names.append(name)
    return names


def build() -> None:
    for state, url in STATE_TABLES.items():
        counties_dir = ROOT / state / "counties"
        if counties_dir.exists():
            for child in counties_dir.iterdir():
                if child.is_dir():
                    child.rmdir()
        else:
            counties_dir.mkdir(parents=True, exist_ok=True)
        counties = _fetch_counties(state, url)
        seeds_path = ROOT / state / "infrastructure" / "seeds" / f"{state.lower()}_counties.csv"
        seeds_path.parent.mkdir(parents=True, exist_ok=True)
        with seeds_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["state", "county", "slug"])
            for county in counties:
                writer.writerow([state, county, _slugify(county)])
                (counties_dir / _slugify(county)).mkdir(parents=True, exist_ok=True)
        print(f"{state}: {len(counties)} counties")


if __name__ == "__main__":
    build()
