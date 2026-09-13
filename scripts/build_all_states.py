from __future__ import annotations

import csv
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path("/root/jailmap/states")

ALL_STATES = [
    ("AL","Alabama"),("AK","Alaska"),("AZ","Arizona"),("AR","Arkansas"),("CA","California"),("CO","Colorado"),
    ("CT","Connecticut"),("DE","Delaware"),("FL","Florida"),("GA","Georgia"),("HI","Hawaii"),("ID","Idaho"),
    ("IL","Illinois"),("IN","Indiana"),("IA","Iowa"),("KS","Kansas"),("KY","Kentucky"),("LA","Louisiana"),
    ("ME","Maine"),("MD","Maryland"),("MA","Massachusetts"),("MI","Michigan"),("MN","Minnesota"),("MS","Mississippi"),
    ("MO","Missouri"),("MT","Montana"),("NE","Nebraska"),("NV","Nevada"),("NH","New Hampshire"),("NJ","New Jersey"),
    ("NM","New Mexico"),("NY","New York"),("NC","North Carolina"),("ND","North Dakota"),("OH","Ohio"),("OK","Oklahoma"),
    ("OR","Oregon"),("PA","Pennsylvania"),("RI","Rhode Island"),("SC","South Carolina"),("SD","South Dakota"),
    ("TN","Tennessee"),("TX","Texas"),("UT","Utah"),("VT","Vermont"),("VA","Virginia"),("WA","Washington"),
    ("WV","West Virginia"),("WI","Wisconsin"),("WY","Wyoming"),("DC","District of Columbia")
]

STATE_TABLES = {code: f"https://en.wikipedia.org/wiki/List_of_counties_in_{name}" for code, name in ALL_STATES}


def _slugify(name: str) -> str:
    cleaned = re.sub(r"\bcounty\b", "", name, flags=re.IGNORECASE).strip()
    return "-".join(cleaned.lower().split())


def _fetch_counties(url: str) -> list[str]:
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


ADAPTER_PY = '''\
from __future__ import annotations

from typing import Any, Dict, List

from ..idaho import AdapterResult


def parse(source: Dict[str, Any]) -> AdapterResult:
    raise NotImplementedError(f"Implement adapter for {source.get('county')}")


if __name__ == "__main__":
    import json
    print(json.dumps(parse({"state":"MT","county":"example"}), indent=2))
'''

CONFIG_PY = '''\
SOURCE_URL = ""
ENABLED = False
COUNTY = "example"
'''

PIPELINE_SH = '''\
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m adapter
'''

INGEST_PY = '''\
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

COUNTIES_DIR = Path(__file__).parent / "counties"


async def run_county_pipeline(county_slug: str) -> bool:
    county_dir = COUNTIES_DIR / county_slug
    if not county_dir.exists():
        print(f"County {county_slug} not found")
        return False

    sys.path.insert(0, str(county_dir))
    try:
        from adapter import parse  # type: ignore
        from config import SOURCE_URL, ENABLED  # type: ignore

        if not ENABLED or not SOURCE_URL:
            print(f"  {county_slug}: disabled")
            return True

        result = parse({"state":"MT","county": county_slug, "source_url": SOURCE_URL})
        print(f"  {county_slug}: fetched {len(result.records)} records status={result.status}")
        return True
    except Exception as e:  # pragma: no cover - bootstrap stub
        print(f"  {county_slug}: ERROR - {e}")
        return False


async def run_all() -> None:
    counties = sorted([d.name for d in COUNTIES_DIR.iterdir() if d.is_dir()])
    print(f"Running ingestion for {len(counties)} counties...")
    results = await asyncio.gather(*[run_county_pipeline(c) for c in counties], return_exceptions=True)
    success = sum(1 for r in results if r is True)
    print(f"Completed: {success}/{len(counties)} successful")


if __name__ == "__main__":
    asyncio.run(run_all())
'''


def build() -> None:
    # clear states tree except shared infrastructure if needed
    for state_dir in ROOT.iterdir():
        if state_dir.is_dir() and state_dir.name in [code for code, _ in ALL_STATES] + ["infrastructure"]:
            for child in state_dir.rglob("*"):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()

    # ensure top-level infrastructure
    (ROOT / "infrastructure" / "seeds").mkdir(parents=True, exist_ok=True)
    (ROOT / "infrastructure" / "seeds" / "all_states.csv").write_text(
        "state_code,state_name\n" + "\n".join(f"{code},{name}" for code, name in ALL_STATES) + "\n",
        encoding="utf-8",
    )
    schema_path = ROOT / "infrastructure" / "schema.sql"
    if not schema_path.exists():
        schema_path.write_text(
            """\
CREATE TABLE IF NOT EXISTS records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state TEXT NOT NULL,
  county TEXT NOT NULL,
  facility_name TEXT,
  source_url TEXT,
  source_type TEXT,
  pulled_at TEXT,
  inmate_id TEXT,
  booking_number TEXT,
  full_name TEXT,
  dob TEXT,
  age INTEGER,
  sex TEXT,
  charges TEXT,
  status TEXT,
  mugshot_url TEXT
);
""",
            encoding="utf-8",
        )

    for code, name in ALL_STATES:
        state_dir = ROOT / code
        (state_dir / "counties").mkdir(parents=True, exist_ok=True)
        (state_dir / "infrastructure" / "seeds").mkdir(parents=True, exist_ok=True)
        if not (state_dir / "ingest.py").exists():
            (state_dir / "ingest.py").write_text(INGEST_PY.replace("MT", code), encoding="utf-8")

    for state, url in STATE_TABLES.items():
        counties = _fetch_counties(url)
        counties_dir = ROOT / state / "counties"
        if counties_dir.exists():
            for child in counties_dir.iterdir():
                if child.is_dir():
                    child.rmdir()
        seeds_path = ROOT / state / "infrastructure" / "seeds" / f"{state.lower()}_counties.csv"
        with seeds_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["state", "county", "slug"])
            for county in counties:
                writer.writerow([state, county, _slugify(county)])
                county_dir = counties_dir / _slugify(county)
                county_dir.mkdir(parents=True, exist_ok=True)
                (county_dir / "adapter.py").write_text(ADAPTER_PY, encoding="utf-8")
                (county_dir / "config.py").write_text(CONFIG_PY.replace("example", _slugify(county)), encoding="utf-8")
                pipeline = county_dir / "pipeline.sh"
                if not pipeline.exists():
                    pipeline.write_text(PIPELINE_SH, encoding="utf-8")
                    pipeline.chmod(0o755)
        print(f"{state}: {len(counties)} counties")


if __name__ == "__main__":
    build()
