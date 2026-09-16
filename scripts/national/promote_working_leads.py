#!/usr/bin/env python3
"""Test all adapter_needed leads and promote working ones to staging_only jurisdictions."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import psycopg
from psycopg.rows import dict_row


def main():
    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)

    # Get all adapter_needed leads
    leads = conn.execute('''
        SELECT q.source_url, q.adapter, q.notes, c.name as county_name, s.abbrev as state
        FROM records.county_ingestion_queue q
        JOIN public."County" c ON c.id = q.county_id
        JOIN public."State" s ON s.id = c."stateId"
        WHERE q.status = 'adapter_needed'
        ORDER BY s.abbrev, c.name
    ''').fetchall()

    print(f"Testing {len(needed)} adapter_needed leads...")

    # Import the adapter
    from backend.adapters.html_roster import fetch

    promoted = 0
    failed = 0

    for r in leads:
        state = r["state"]
        county = r["county_name"]
        url = r["source_url"]

        # Check if jurisdiction already exists
        existing = conn.execute(
            "SELECT id FROM records.jurisdictions WHERE state=%s AND county=%s AND facility_name=%s",
            (state, county, f"{county} County Jail")
        ).fetchone()

        if existing:
            print(f"  SKIP {state}/{county}: jurisdiction already exists")
            continue

        source = {
            "state": state,
            "county": county,
            "facility_name": f"{county} County Jail",
            "source_url": url,
        }

        try:
            records = fetch(source)
            if len(records) > 0:
                # Create staging_only jurisdiction
                conn.execute(
                    """INSERT INTO records.jurisdictions 
                       (state, county, facility_name, source_url, adapter, authorization_reference, enabled, staging_only, review_status)
                       VALUES (%s, %s, %s, %s, %s, %s, false, true, 'verified')""",
                    (state, county, f"{county} County Jail", url, 'html_roster_staging', 'public_roster')
                )
                conn.commit()
                print(f"  PROMOTED {state}/{county}: {len(records)} records (staging_only)")
                promoted += 1
            else:
                print(f"  EMPTY {state}/{county}: 0 records")
                failed += 1
        except Exception as e:
            print(f"  FAIL {state}/{county}: {str(e)[:60]}")
            failed += 1

    print(f"\nResult: {promoted} promoted, {failed} failed/empty")
    conn.close()


if __name__ == "__main__":
    main()
