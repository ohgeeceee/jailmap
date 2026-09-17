"""Run daily: python -m backend.ingest. Never accepts user-supplied endpoints."""
import os
from urllib.parse import urlsplit
import httpx
from backend.db import pool
from backend.normalize import normalize
from backend.staging import json_safe, prepare_staging_rows

def standard_json(source):
    # Operators must approve both the source entry and exact host. Enforce egress
    # network policy as well; this allowlist is not a DNS-rebinding firewall.
    url = source['source_url']
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.username or parsed.password
        or parsed.port not in (None, 443)
        or parsed.hostname not in os.environ.get('SOURCE_ALLOWED_HOSTS', '').split(',')):
        raise ValueError('Source endpoint is not authorized')
    cursor = None
    seen = set()
    rows = []
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        for _ in range(1000):
            with client.stream('GET', url, params={'cursor': cursor} if cursor else {}) as response:
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > 10_000_000:
                        raise ValueError('Source page too large')
            import json
            payload = json.loads(content)
            rows.extend(normalize(row) for row in payload['items'])
            if len(rows) > 100_000:
                raise ValueError('Source exceeds configured record limit')
            cursor = payload.get('next_cursor')
            if cursor is None:
                return rows
            if not isinstance(cursor, str) or len(cursor) > 2000 or cursor in seen:
                raise ValueError('Invalid or repeated pagination cursor')
            seen.add(cursor)
    raise ValueError('Source exceeds pagination limit')

# Add authorized vendor, Socrata or RSS adapters here. Each returns this same
# complete normalized contract; RSS must not infer release from an absent entry.
from backend.fulton import fetch as fulton_staging
from backend.fulton import fetch_public as fulton_public
from backend.adapters import bonneville_html, franklin_html, power_html
from backend.adapters import minnehaha_html
from backend.adapters import mt_zuercher, mt_flathead, mt_missoula, mt_yellowstone
from backend.adapters import mt_prairie, mt_lake, mt_beaverhead, mt_lewis_and_clark
from backend.adapters import html_roster
from backend.adapters import socrata
from backend.adapters import evo_json, citizenrims
from backend.adapters import tyler_odyssey
ADAPTERS = {'standard_json': standard_json, 'fulton_socrata_staging': fulton_staging,
            'fulton_public_roster': fulton_public,
            'bonneville_html_staging': lambda source: bonneville_html.parse(source).records,
            'franklin_html_staging': lambda source: franklin_html.parse(source).records,
            'power_html_staging': lambda source: power_html.parse(source).records,
            'minnehaha_html_staging': minnehaha_html.fetch,
            'html_roster_staging': html_roster.fetch,
            'socrata_staging': socrata.fetch,
            'mt_zuercher_staging': lambda source: mt_zuercher.fetch(source).records,
            'flathead_html_staging': lambda source: mt_flathead.fetch(source).records,
            'missoula_html_staging': lambda source: mt_missoula.fetch(source).records,
            'yellowstone_html_staging': lambda source: mt_yellowstone.fetch(source).records,
            'prairie_html_staging': lambda source: mt_prairie.fetch(source).records,
            'lake_pdf_staging': lambda source: mt_lake.fetch(source).records,
            'beaverhead_pdf_staging': lambda source: mt_beaverhead.fetch(source).records,
            'lewis_and_clark_pdf_staging': lambda source: mt_lewis_and_clark.fetch(source).records,
            'tyler_odyssey_staging': lambda source: tyler_odyssey.fetch(source).records,
            'evo_json_staging': lambda source: evo_json.fetch(source).records,
            'citizenrims_portal': lambda source: citizenrims.fetch(source).records}

def upsert(connection, jurisdiction_id, row):
    from datetime import datetime,timezone
    booking = connection.execute('''INSERT INTO records.inmates
    (jurisdiction_id,booking_number,first_name,last_name,dob,booking_date,mugshot_url,source_updated_at,visibility,observed_at,booking_date_precision,booking_timezone)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (jurisdiction_id,booking_number) DO UPDATE SET
      first_name=EXCLUDED.first_name,last_name=EXCLUDED.last_name,dob=EXCLUDED.dob,
      booking_date=EXCLUDED.booking_date,mugshot_url=EXCLUDED.mugshot_url,
      source_updated_at=EXCLUDED.source_updated_at,observed_at=EXCLUDED.observed_at,
      booking_date_precision=EXCLUDED.booking_date_precision,booking_timezone=EXCLUDED.booking_timezone,
      visibility=CASE WHEN records.inmates.visibility='suppressed' THEN 'suppressed' ELSE EXCLUDED.visibility END,
      version=records.inmates.version+1
    WHERE records.inmates.source_updated_at <= EXCLUDED.source_updated_at
    RETURNING id,version''', (jurisdiction_id, *[row[key] for key in (
        'booking_number','first_name','last_name','dob','booking_date','mugshot_url','source_updated_at','visibility')],
            row.get('observed_at',datetime.now(timezone.utc)),row.get('booking_date_precision','timestamp'),row.get('booking_timezone','UTC'))).fetchone()
    if not booking:
        return
    # Replace complete child collections atomically; deleted charges do not linger.
    connection.execute('DELETE FROM records.charges WHERE inmate_id=%s', (booking['id'],))
    connection.execute('DELETE FROM records.bonds WHERE inmate_id=%s', (booking['id'],))
    for charge in row['charges']:
        connection.execute('''INSERT INTO records.charges(inmate_id,source_id,statute,description,severity)
            VALUES (%s,%s,%s,%s,%s)''', (booking['id'], charge['id'],charge['statute'],charge['description'],charge['severity']))
    for bond in row['bonds']:
        connection.execute('''INSERT INTO records.bonds(inmate_id,source_id,amount,type,status)
            VALUES (%s,%s,%s,%s,%s)''', (booking['id'],bond['id'],bond['amount'],bond['type'],bond['status']))
    connection.execute('''INSERT INTO records.search_outbox(inmate_id,version) VALUES (%s,%s)
        ON CONFLICT(inmate_id) DO UPDATE SET version=EXCLUDED.version,queued_at=now()''',
        (booking['id'],booking['version']))

def run(state=None, county=None, jurisdiction=None, dry_run=False):
    failed = False
    with pool:
        with pool.connection() as connection:
            sources = connection.execute('''SELECT * FROM records.jurisdictions
                WHERE review_status='verified' AND (enabled OR staging_only OR (%s AND id=%s::uuid)) AND (%s::text IS NULL OR state=%s)
                AND (%s::text IS NULL OR county=%s)
                AND (%s::uuid IS NULL OR id=%s::uuid) ORDER BY state,county,facility_name''',
                (dry_run,jurisdiction,state,state,county,county,jurisdiction,jurisdiction)).fetchall()
        if not sources:
            print('No enabled sources match; no bookings ingested.')
            return
        for source in sources:
            run_id = None
            try:
                if source['review_status'] != 'verified' or source['authorization_reference'].strip().lower() in ('', 'pending'):
                    raise ValueError('Source authorization missing')
                # Lock before fetching, so overlapping schedulers cannot apply an older snapshot last.
                with pool.connection() as guard:
                    locked = guard.execute('SELECT pg_try_advisory_lock(hashtextextended(%s,0)) AS locked',
                                           (str(source['id']),)).fetchone()['locked']
                    guard.commit()
                    if not locked:
                        print(f"Source {source['id']}: already running; skipped")
                        continue
                    try:
                        if not dry_run:
                            with pool.connection() as connection:
                                run_id = connection.execute('''INSERT INTO records.ingestion_runs(jurisdiction_id,status)
                                    VALUES (%s,'running') RETURNING id''', (source['id'],)).fetchone()['id']
                        rows = ADAPTERS[source['adapter']](source)
                        staging_rows = prepare_staging_rows(rows) if source['staging_only'] else None
                        if source['staging_only']:
                            keys = [row[0] for row in staging_rows]
                        else:
                            keys = [row['booking_number'] for row in rows]
                            if len(keys) != len(set(keys)):
                                raise ValueError('Duplicate booking keys in source snapshot')
                        if not dry_run:
                            with pool.connection() as connection, connection.transaction():
                                current = connection.execute('SELECT enabled,staging_only,review_status FROM records.jurisdictions WHERE id=%s FOR UPDATE', (source['id'],)).fetchone()
                                if not (current['enabled'] or current['staging_only']) or current['review_status'] != 'verified' or current['staging_only'] != source['staging_only']:
                                    raise ValueError('Source disabled during fetch')
                                if source['staging_only']:
                                    from psycopg.types.json import Jsonb
                                    import json
                                    # Complete staging snapshot replaces only staging rows, never public bookings.
                                    connection.execute('DELETE FROM records.staged_bookings WHERE jurisdiction_id=%s',(source['id'],))
                                    for booking_number, row, source_snapshot_at in staging_rows:
                                        connection.execute('''INSERT INTO records.staged_bookings(jurisdiction_id,booking_number,payload,source_snapshot_at)
                                            VALUES (%s,%s,%s,%s)''',(source['id'],booking_number,Jsonb(json_safe(row)),source_snapshot_at))
                                else:
                                    for row in rows:
                                        upsert(connection, source['id'], row)
                                    if source['adapter']=='fulton_public_roster':
                                        # A complete current roster establishes non-listing, not release.
                                        hidden=connection.execute('''UPDATE records.inmates SET visibility='unlisted',version=version+1
                                            WHERE jurisdiction_id=%s AND visibility='public' AND NOT (booking_number=ANY(%s))
                                            RETURNING id,version''',(source['id'],keys)).fetchall()
                                        for record in hidden:
                                            connection.execute('''INSERT INTO records.search_outbox(inmate_id,version) VALUES (%s,%s)
                                                ON CONFLICT(inmate_id) DO UPDATE SET version=EXCLUDED.version,queued_at=now()''',
                                                (record['id'],record['version']))
                                connection.execute('UPDATE records.jurisdictions SET last_success_at=now() WHERE id=%s', (source['id'],))
                                connection.execute("UPDATE records.ingestion_runs SET status='success',finished_at=now(),record_count=%s WHERE id=%s", (len(rows),run_id))
                        print(f"{source['state']} / {source['county']}: {len(rows)} validated records; " + ('dry run, no writes' if dry_run else ('staged privately' if source['staging_only'] else 'committed')))
                    finally:
                        guard.execute('SELECT pg_advisory_unlock(hashtextextended(%s,0))', (str(source['id']),))
                        guard.commit()
            except Exception as exc:
                if run_id is not None:
                    with pool.connection() as connection:
                        connection.execute("UPDATE records.ingestion_runs SET status='failed',finished_at=now(),error_type=%s,error_detail=%s WHERE id=%s", (type(exc).__name__,str(exc)[:800],run_id))
                # Avoid logging raw payloads, credentials or personal information.
                print(f"Source {source['id']} failed ({type(exc).__name__}); transaction not applied")
                failed = True
    if failed:
        raise SystemExit(1)

if __name__ == '__main__':
    import argparse
    from uuid import UUID
    from backend.national_seed import STATES
    parser = argparse.ArgumentParser(description='Ingest verified sources, optionally one state/county at a time')
    parser.add_argument('--state', type=str.upper, choices=sorted(STATES))
    parser.add_argument('--county', help='Exact jurisdiction county name')
    parser.add_argument('--jurisdiction', type=UUID)
    parser.add_argument('--dry-run', action='store_true', help='Fetch and validate without database writes')
    args = parser.parse_args()
    run(args.state,args.county,args.jurisdiction,args.dry_run)
