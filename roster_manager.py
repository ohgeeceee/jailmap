#!/usr/bin/env python3
"""Roster manager CLI over the existing backend ingest pipeline.

Thin wrapper: does NOT reimplement fetching or upserting. All heavy lifting
lives in backend.ingest (adapters, registry, advisory locks) and
records.ingestion_runs (status / counts / errors live here, not a separate
scrape_logs table).

Usage:
    python -m roster_manager --run [STATE|county=NAME|all]
    python -m roster_manager --status [--limit 50]
    python -m roster_manager --retry-failed
    python -m roster_manager --test county=NAME [--jurisdiction UUID]

Requires DATABASE_URL (same env as backend.ingest). Run from the jailmap
project root:  cd /root/jailmap && python -m roster_manager ...
"""
import argparse
import sys

import os

import psycopg
from psycopg.rows import dict_row


def _query(sql, params=()):
    """One-off connection for manager lookups. Do NOT touch backend.db.pool
    here: backend.ingest.run() owns that pool (`with pool:`) and a closed
    psycopg pool cannot be reopened."""
    with psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row) as conn:
        return conn.execute(sql, params).fetchall()


def _fetch_sources(state, county, jurisdiction):
    return _query('''
        SELECT id, state, county, facility_name, adapter, staging_only
        FROM records.jurisdictions
        WHERE review_status='verified' AND (enabled OR staging_only)
          AND (%s::text IS NULL OR state=%s)
          AND (%s::text IS NULL OR county=%s)
          AND (%s::uuid IS NULL OR id=%s::uuid)
        ORDER BY state, county, facility_name
    ''', (state, state, county, county, jurisdiction, jurisdiction))


def cmd_run(state, county, jurisdiction):
    sources = _fetch_sources(state, county, jurisdiction)
    if not sources:
        print('No enabled/verified sources match; nothing to run.')
        return 1
    print(f'{len(sources)} source(s) selected')
    rc = 0
    for s in sources:
        print(f"  {s['state']}/{s['county']} ({s['facility_name']}) adapter={s['adapter']}")
    return _run_ingest(sources)


def _run_ingest(sources, dry_run=False):
    """Run backend.ingest one source at a time as a subprocess.

    backend.ingest.run() is one-shot per process: `with pool:` CLOSES the
    pool on exit, so a second in-process call raises PoolClosed. Shelling
    out keeps its transaction/locking semantics untouched.
    """
    import subprocess
    rc = 0
    for s in sources:
        cmd = [sys.executable, '-m', 'backend.ingest', '--jurisdiction', str(s['id'])]
        if dry_run:
            cmd.append('--dry-run')
        print(f"-> {s['state']}/{s['county']} ({s['facility_name']})")
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            print(f"   FAILED (exit {proc.returncode})")
            rc = 1
    return rc


def cmd_status(limit):
    rows = _query('''
        SELECT r.state, r.county, r.facility_name,
               i.status, i.record_count, i.started_at, i.finished_at, i.error_type
        FROM records.ingestion_runs i
        JOIN records.jurisdictions r ON r.id = i.jurisdiction_id
        WHERE i.finished_at IS NOT NULL
          AND i.id IN (
            SELECT MAX(id) FROM records.ingestion_runs
            WHERE finished_at IS NOT NULL GROUP BY jurisdiction_id)
        ORDER BY i.finished_at DESC
        LIMIT %s
    ''', (limit,))
    totals = _query('''
        SELECT status, COUNT(*) AS n FROM records.ingestion_runs
        WHERE finished_at IS NOT NULL GROUP BY status
    ''')
    print(f"{'STATE':<6} {'COUNTY':<16} {'STATUS':<8} {'RECS':>6}  "
          f"{'STARTED (UTC)':<20} {'DUR(s)':>7}  ERROR")
    for r in rows:
        dur = ''
        if r['started_at'] and r['finished_at']:
            dur = f"{(r['finished_at'] - r['started_at']).total_seconds():.1f}"
        print(f"{r['state'] or '':<6} {r['county'] or '':<16} {r['status']:<8} "
              f"{r['record_count'] if r['record_count'] is not None else '-':>6}  "
              f"{r['started_at'].strftime('%Y-%m-%d %H:%M:%S') if r['started_at'] else '-':<20} "
              f"{dur:>7}  {r['error_type'] or ''}")
    print('\nAll-time run counts by status:')
    for t in totals:
        print(f"  {t['status']}: {t['n']}")
    return 0


def cmd_retry_failed():
    failed = _query('''
        SELECT DISTINCT r.state, r.county, r.id
        FROM records.ingestion_runs i
        JOIN records.jurisdictions r ON r.id = i.jurisdiction_id
        WHERE i.finished_at IS NOT NULL
          AND i.id IN (
            SELECT MAX(id) FROM records.ingestion_runs
            WHERE finished_at IS NOT NULL GROUP BY jurisdiction_id)
          AND (i.status = 'failed' OR COALESCE(i.record_count, 0) = 0)
    ''')
    if not failed:
        print('No failed or zero-record sources from the last completed run.')
        return 0
    print(f'Retrying {len(failed)} failed/empty source(s)')
    return _run_ingest(failed)


def cmd_test(county, jurisdiction):
    # Dry-run: fetch + validate + print, zero DB writes.
    sources = _fetch_sources(None, county, jurisdiction)
    if not sources:
        print('No enabled/verified sources match; nothing to test.')
        return 1
    for s in sources:
        print(f"TEST {s['state']}/{s['county']} adapter={s['adapter']} (dry run, no writes)")
    return _run_ingest(sources, dry_run=True)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--run', metavar='TARGET',
                   help="STATE abbr | county=Name | all")
    g.add_argument('--status', action='store_true')
    g.add_argument('--retry-failed', action='store_true')
    g.add_argument('--test', metavar='TARGET',
                   help="county=Name dry-run, prints results, no writes")
    p.add_argument('--jurisdiction', help='UUID, narrows --run/--test')
    p.add_argument('--limit', type=int, default=50, help='rows for --status')
    args = p.parse_args()

    state = county = None
    target = args.run or args.test
    if target:
        if target.lower() == 'all':
            pass
        elif target.lower().startswith('county='):
            county = target.split('=', 1)[1]
        else:
            state = target.upper()
    jurisdiction = args.jurisdiction
    if args.jurisdiction:
        from uuid import UUID
        jurisdiction = UUID(args.jurisdiction)

    if args.status:
        sys.exit(cmd_status(args.limit))
    if args.run:
        sys.exit(cmd_run(state, county, jurisdiction))
    if args.retry_failed:
        sys.exit(cmd_retry_failed())
    if args.test:
        sys.exit(cmd_test(county, jurisdiction))


if __name__ == '__main__':
    main()
