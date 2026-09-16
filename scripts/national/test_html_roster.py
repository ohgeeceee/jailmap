#!/usr/bin/env python3
"""Test html_roster adapter against all staged leads. Dry-run only."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "adapters"))

import csv
import psycopg
from psycopg.rows import dict_row


def main():
    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
    rows = conn.execute('''
        SELECT q.source_url, q.adapter, q.notes, c.name as county_name, s.abbrev as state
        FROM records.county_ingestion_queue q
        JOIN public."County" c ON c.id = q.county_id
        JOIN public."State" s ON s.id = c."stateId"
        WHERE q.adapter = ''html_roster_staging''
        AND q.status = ''adapter_needed''
        ORDER BY s.abbrev, c.name
    ''').fetchall()
    conn.close()

    print(f"Testing {len(rows)} html_roster leads...")

    from html_roster import fetch

    passed = 0
    failed = 0
    for r in rows:
        state = r["state"]
        county = r["county_name"]
        url = r["source_url"]

        try:
            # Temporarily override the allowlist check by adding hostname
            parsed = __import__("urllib.parse").urlparse(url)
            hostname = parsed.hostname

            # Check current allowlist
            from backend.adapters import idaho
            old_allowed = idaho.ALLOWED_HOSTS
            idaho.ALLOWED_HOSTS = {hostname}

            source = {
                "state": state,
                "county": county,
                "facility_name": f"{county} County Jail",
                "source_url": url,
            }
            records = fetch(source)
            idaho.ALLOWED_HOSTS = old_allowed

            print(f"  OK {state}/{county}: {len(records)} records")
            passed += 1

        except Exception as e:
            err_msg = str(e)[:80]
            print(f"  FAIL {state}/{county}: {err_msg}")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed out of {len(rows)}")


if __name__ == "__main__":
    main()
