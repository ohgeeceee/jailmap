#!/usr/bin/env python3
"""Probe and test parsing for blocked jurisdictions in missing states."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app/backend")

import httpx
from backend.db import pool


MISSING_STATES = ["AK", "CT", "KS", "KY", "MD", "NV", "OR", "RI", "SD", "VT", "WI"]


def main():
    pool.open()
    with pool.connection() as conn:
        jurisdictions = conn.execute("""
            SELECT id, state, county, source_url, adapter, review_status, staging_only, enabled
            FROM records.jurisdictions
            WHERE state = ANY(%s)
            ORDER BY state, county
        """, (MISSING_STATES,)).fetchall()

    client = httpx.Client(
        timeout=15,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0)"},
    )

    results = []
    for j in jurisdictions:
        state, county, url = j["state"], j["county"], j["source_url"]
        print(f"\n{state}/{county}: {url}")

        # Probe URL
        try:
            r = client.get(url, timeout=15, follow_redirects=True)
            text = r.text.lower()
            keywords = ["inmate", "roster", "booking", "arrest", "custody", "detention", "jail", "sheriff"]
            kw_count = sum(1 for kw in keywords if kw in text)
            title = None
            if "<title>" in text:
                title = text.split("<title>")[1].split("</title>")[0][:100]
            print(f"  HTTP {r.status_code} | {len(r.text)} chars | roster_kw={kw_count} | title={title}")
            has_roster = kw_count >= 2 and r.status_code == 200
        except Exception as e:
            print(f"  ERROR: {e}")
            has_roster = False

        # Test parser if URL looks promising
        if has_roster:
            try:
                from backend.adapters import html_roster
                source = {"state": state, "county": county, "source_url": url}
                result = html_roster.fetch(source)
                records = result.records if hasattr(result, "records") else result
                print(f"  PARSER: {len(records)} records")
                if records:
                    print(f"  SAMPLE: {json.dumps(records[0], default=str)[:300]}")
                results.append({
                    "state": state, "county": county, "url": url,
                    "http_status": r.status_code, "parser_records": len(records),
                    "sample": records[0] if records else None,
                })
            except Exception as e:
                print(f"  PARSER ERROR: {e}")

    print(f"\n\n=== SUMMARY ===")
    for r in results:
        print(f"  {r['state']}/{r['county']}: {r['parser_records']} records")
    print(f"Total jurisdictions with parseable records: {len(results)}")


if __name__ == "__main__":
    main()
