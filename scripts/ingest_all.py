#!/usr/bin/env python3
"""Unified jail roster ingestion pipeline.

Reads adapters and catalog, ingests all counties with working adapters.

Usage:
    python3 scripts/ingest_all.py --dry-run
    python3 scripts/ingest_all.py --state AL
    python3 scripts/ingest_all.py --all
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "adapters"))


def get_db():
    import psycopg
    return psycopg.connect(os.environ['DATABASE_URL'])


def ensure_jurisdiction(conn, *, state: str, county: str, facility: str, source_url: str) -> str:
    row = conn.execute(
        "SELECT id FROM records.jurisdictions WHERE state=%s AND county=%s AND facility_name=%s",
        (state, county, facility)
    ).fetchone()
    if row:
        return str(row[0])
    row = conn.execute(
        """INSERT INTO records.jurisdictions (state, county, facility_name, source_url, adapter, authorization_reference, enabled)
           VALUES (%s, %s, %s, %s, %s, %s, true) RETURNING id""",
        (state, county, facility, source_url, 'county_adapter', 'public_roster')
    ).fetchone()
    conn.commit()
    return str(row[0])


def ingest_county(conn, state: str, county: str, adapter, source_url: str, *, dry_run: bool = False):
    facility = f"{county} County Jail"
    result = {"state": state, "county": county, "records": 0, "status": "ok"}
    
    try:
        adapter_result = adapter({"source_url": source_url, "county": county, "facility_name": facility})
        records = adapter_result.records
        result["records"] = len(records)
        
        if dry_run:
            result["status"] = "dry_run"
            return result
        
        if not records:
            result["status"] = "empty"
            return result
        
        jurisdiction_id = ensure_jurisdiction(conn, state=state, county=county, facility=facility, source_url=source_url)
        
        inserted = 0
        for rec in records:
            booking_number = rec.get("booking_number") or f"{state}-{county}-{hash(rec.get('full_name', '')) % 10000000:07d}"
            
            existing = conn.execute(
                "SELECT id FROM records.inmates WHERE jurisdiction_id=%s AND booking_number=%s",
                (jurisdiction_id, booking_number)
            ).fetchone()
            if existing:
                continue
            
            conn.execute(
                """INSERT FROM records.inmates 
                    (jurisdiction_id, booking_number, first_name, last_name, booking_date,
                     source_updated_at, visibility, age, sex, race)
                   VALUES (%s, %s, %s, %s, %s, now(), 'public', %s, %s, %s)""",
                (jurisdiction_id, booking_number,
                 rec.get("first_name", ""), rec.get("last_name", ""),
                 rec.get("booking_date"),
                 rec.get("age"), rec.get("sex"), rec.get("race"))
            )
            
            inserted += 1
        
        conn.commit()
        result["inserted"] = inserted
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]
    
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", help="Single state to ingest")
    parser.add_argument("--all", action="store_true", help="Ingest all states")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    # Import available adapters
    from alabama import ALABAMA_ADAPTERS, COUNTY_URLS as AL_URLS
    
    STATE_ADAPTERS = {
        "AL": (ALABAMA_ADAPTERS, AL_URLS),
    }
    
    conn = get_db()
    results = []
    start = time.time()
    
    for state, (adapters, urls) in STATE_ADAPTERS.items():
        if args.state and state != args.state:
            continue
        
        print(f"\n=== {state} ===")
        for county, adapter_name in adapters.items():
            url = urls.get(county, "")
            adapter = ALABAMA_ADAPTERS.get(adapter_name)
            if not adapter:
                continue
            
            result = ingest_county(conn, state, county, adapter, url, dry_run=args.dry_run)
            results.append(result)
            print(f"  {county}: {result['records']} records ({result['status']})")
    
    elapsed = time.time() - start
    total_records = sum(r.get("records", 0) for r in results)
    print(f"\nTotal: {total_records} records in {elapsed:.1f}s")
    
    if args.json:
        print(json.dumps(results, indent=2))
    
    conn.close()


if __name__ == "__main__":
    main()
