#!/usr/bin/env python3
"""Import crawl leads as staging-only jurisdictions.

Reads sheriff-crawl-leads.csv and inserts new jurisdictions into
records.jurisdictions with staging_only=true, enabled=false, review_status='verified'.
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

REPO = Path(os.environ.get('JAILMAP_REPO') or '/root/jailmap')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=REPO / 'data' / 'national' / 'sheriff-crawl-leads.csv')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    with psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row) as conn:
        existing = conn.execute("SELECT source_url FROM records.jurisdictions").fetchall()
        existing_urls = {r['source_url'] for r in existing}

        with args.input.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader if r['access_status'] == 'needs_adapter' and r['source_kind'] in ('zuercher_portal', 'socrata_open_data_portal', 'citizenrims_portal', 'html_roster', 'smartweb_portal', 'tyler_jailtracker_portal', 'tyler_odyssey_portal', 'pdf_roster')]

        new_rows = [r for r in rows if r['source_url'] not in existing_urls]
        if args.limit:
            new_rows = new_rows[:args.limit]

        print(f'{len(new_rows)} new jurisdictions to import (from {len(rows)} leads, {len(rows) - len(new_rows)} already exist)')

        if args.dry_run:
            for r in new_rows:
                print(f"  {r['state']}/{r['county']}: {r['adapter_strategy']} - {r['source_url']}")
            return

        inserted = 0
        skipped = 0
        for r in new_rows:
            try:
                with conn.transaction():
                    conn.execute('''INSERT INTO records.jurisdictions(
                        id, state, county, facility_name, source_url, adapter,
                        staging_only, enabled, review_status, authorization_reference
                    ) VALUES (%s,%s,%s,%s,%s,%s,true,false,'verified','crawl-2026-09-15')
                    ON CONFLICT (state, county, facility_name) DO NOTHING''',
                        (str(uuid4()), r['state'], r['county'], r['county'] + ' County Jail',
                         r['source_url'], r['adapter_strategy']))
                inserted += 1
            except Exception as e:
                print(f"  SKIP {r['state']}/{r['county']}: {e}")
                skipped += 1
                conn.rollback()
        print(f'Inserted {inserted} jurisdictions, skipped {skipped}')


if __name__ == '__main__':
    main()
