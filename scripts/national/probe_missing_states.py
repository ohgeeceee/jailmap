#!/usr/bin/env python3
"""Probe blocked jurisdictions in missing states to find actual roster URLs."""
import csv
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import httpx

MISSING_STATES = ["AK", "CT", "KS", "KY", "MD", "NV", "OR", "RI", "SD", "VT", "WI"]


def get_db():
    import psycopg
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=lambda cur, row: dict(zip([d.name for d in cur.description], row))) if False else psycopg.connect(os.environ["DATABASE_URL"])


def probe_url(url: str, client: httpx.Client):
    try:
        r = client.get(url, timeout=15, follow_redirects=True)
        text = r.text.lower()
        keywords = ["inmate", "roster", "booking", "arrest", "custody", "detention", "jail", "sheriff"]
        has_roster = sum(1 for kw in keywords if kw in text)
        return {
            "status_code": r.status_code,
            "length": len(r.text),
            "final_url": str(r.url),
            "roster_keywords": has_roster,
            "title": text.split("<title>")[1].split("</title>")[0][:100] if "<title>" in text else None,
        }
    except Exception as e:
        return {"error": str(e)[:200]}


def main():
    import psycopg.rows
    conn = get_db()
    conn.row_factory = psycopg.rows.dict_row

    client = httpx.Client(
        timeout=15,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0)"},
    )

    jurisdictions = conn.execute("""
        SELECT id, state, county, adapter, source_url, review_status, staging_only
        FROM records.jurisdictions
        WHERE state = ANY(%s)
        ORDER BY state, county
    """, (MISSING_STATES,)).fetchall()

    print(f"Probing {len(jurisdictions)} blocked jurisdictions in {len(MISSING_STATES)} states...\n")

    for j in jurisdictions:
        state, county, url = j["state"], j["county"], j["source_url"]
        print(f"  {state}/{county}: {url}")
        result = probe_url(url, client)
        print(f"    -> {json.dumps(result)}")

    conn.close()


if __name__ == "__main__":
    main()
