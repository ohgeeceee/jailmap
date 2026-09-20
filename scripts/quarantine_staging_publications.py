#!/usr/bin/env python3
"""Audit or quarantine records published through the generic HTML staging adapter.

Default mode is read-only. Pass --apply to disable affected jurisdictions,
restore staging_only, suppress their bookings, and enqueue search removals.
Suppression is reversible and preserves the records for incident review.
"""
import argparse
import os

import psycopg
from psycopg.rows import dict_row


AUDIT_SQL = """
SELECT j.id, j.state, j.county, j.facility_name, j.adapter, j.source_url,
       j.enabled, j.staging_only,
       count(i.id) AS booking_count,
       count(i.id) FILTER (WHERE i.visibility = 'public') AS public_count,
       count(i.id) FILTER (WHERE i.booking_number LIKE 'SYN-%') AS synthetic_count,
       min(i.observed_at) AS first_observed_at,
       max(i.observed_at) AS last_observed_at
FROM records.jurisdictions j
LEFT JOIN records.inmates i ON i.jurisdiction_id = j.id
WHERE j.adapter = 'html_roster_staging'
  AND (NOT j.staging_only OR i.visibility = 'public')
GROUP BY j.id
ORDER BY public_count DESC, j.state, j.county
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    with psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row) as connection:
        rows = connection.execute(AUDIT_SQL).fetchall()
        for row in rows:
            print(dict(row))
        if not args.apply:
            print(f'Audit only: {len(rows)} affected staging-adapter jurisdictions')
            return
        with connection.transaction():
            affected = connection.execute("""
                UPDATE records.jurisdictions
                SET enabled=false, staging_only=true
                WHERE adapter = 'html_roster_staging'
                  AND NOT staging_only
                RETURNING id
            """).fetchall()
            ids = [row['id'] for row in affected]
            suppressed = []
            if ids:
                suppressed = connection.execute("""
                    UPDATE records.inmates
                    SET visibility='suppressed', version=version+1
                    WHERE jurisdiction_id = ANY(%s)
                      AND visibility <> 'suppressed'
                    RETURNING id, version
                """, (ids,)).fetchall()
                with connection.cursor() as cursor:
                    cursor.executemany("""
                        INSERT INTO records.search_outbox(inmate_id, version)
                        VALUES (%s, %s)
                        ON CONFLICT(inmate_id) DO UPDATE
                        SET version=EXCLUDED.version, queued_at=now()
                    """, [(row['id'], row['version']) for row in suppressed])
        print(f'Quarantined {len(affected)} jurisdictions; suppressed {len(suppressed)} bookings')


if __name__ == '__main__':
    main()
