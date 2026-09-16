#!/usr/bin/env python3
"""JailMap national coverage audit — the honest number.

Reports what is actually ingesting, never what is scaffolded. A county directory is
not a source, and a stub adapter is not coverage.

Run via scripts/national/run.sh audit_coverage.py [--markdown|--json]

Exit code is 0 always; this is a reporting tool, not a gate.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Mounted read-only by scripts/national/run.sh
REPO = Path(os.environ.get('JAILMAP_REPO') or '/src')


def connect():
    import psycopg
    return psycopg.connect(os.environ['DATABASE_URL'])


def stub_counts() -> dict:
    """Count real vs stub adapters. This is the number that kills the illusion."""
    adapters = list((REPO / 'states').rglob('adapter.py'))
    stubs = 0
    for path in adapters:
        try:
            if 'NotImplementedError' in path.read_text(errors='ignore'):
                stubs += 1
        except OSError:
            pass
    backend = sorted((REPO / 'backend' / 'adapters').glob('*.py'))
    registered = 0
    ingest = REPO / 'backend' / 'ingest.py'
    if ingest.exists():
        text = ingest.read_text(errors='ignore')
        registered = text.count('_html_staging') + text.count('_json_staging')
    return {'county_adapter_files': len(adapters), 'county_adapter_stubs': stubs,
            'county_adapters_real': len(adapters) - stubs,
            'backend_adapter_files': len([p for p in backend if p.name != '__init__.py']),
            'backend_adapters_registered_approx': registered}


def audit() -> dict:
    with connect() as connection:
        cur = connection.cursor()

        cur.execute('''SELECT (SELECT count(*) FROM "County"),
            (SELECT count(*) FROM "Jail"),
            (SELECT count(*) FROM "Jail" WHERE website NOT LIKE '%census.gov%'),
            (SELECT count(*) FROM "Jail" WHERE "isActive")''')
        counties, jails, jails_real_site, jails_active = cur.fetchone()

        cur.execute('''SELECT count(*),
            count(*) FILTER (WHERE enabled),
            count(*) FILTER (WHERE review_status='verified'),
            count(*) FILTER (WHERE staging_only),
            count(DISTINCT county_id) FROM records.jurisdictions''')
        registered, enabled, verified, staging, counties_with_source = cur.fetchone()

        # The only number that means anything: did it actually produce records recently?
        # Count successful jurisdictions only — a source that ran and failed every time
        # is not coverage.
        cur.execute("""SELECT count(*) FILTER (WHERE succeeded),
            count(*) FROM (
              SELECT jurisdiction_id, bool_or(status='success') AS succeeded
              FROM records.ingestion_runs
              WHERE started_at > now() - interval '7 days'
              GROUP BY jurisdiction_id) r""")
        ingesting_7d, ran_7d = cur.fetchone()

        cur.execute('''SELECT count(*), count(*) FILTER (WHERE visibility='public'),
            count(DISTINCT jurisdiction_id) FROM records.inmates''')
        records, public_records, jurisdictions_with_records = cur.fetchone()

        cur.execute('''SELECT s.abbrev, s.name,
            (SELECT count(*) FROM "County" c WHERE c."stateId"=s.id),
            (SELECT count(*) FROM "Jail" jl WHERE jl."stateId"=s.id),
            COALESCE(r.registered,0), COALESCE(r.enabled,0),
            COALESCE(a.ingesting,0), COALESCE(b.records,0)
            FROM "State" s
            LEFT JOIN (SELECT state, count(*) AS registered,
                    count(*) FILTER (WHERE enabled) AS enabled
                FROM records.jurisdictions GROUP BY state) r ON r.state=s.abbrev
            LEFT JOIN (SELECT j.state, count(DISTINCT x.jurisdiction_id) AS ingesting
                FROM records.ingestion_runs x JOIN records.jurisdictions j ON j.id=x.jurisdiction_id
                WHERE x.status='success' AND x.started_at > now() - interval '7 days'
                GROUP BY j.state) a ON a.state=s.abbrev
            LEFT JOIN (SELECT j.state, count(*) AS records FROM records.inmates i
                JOIN records.jurisdictions j ON j.id=i.jurisdiction_id GROUP BY j.state) b
                ON b.state=s.abbrev
            ORDER BY COALESCE(a.ingesting,0) DESC, COALESCE(r.enabled,0) DESC, s.name''')
        states = [{'state': r[0], 'name': r[1], 'counties': r[2], 'jails': r[3],
                   'registered': r[4], 'enabled': r[5], 'ingesting_7d': r[6],
                   'records': r[7]} for r in cur.fetchall()]

    return {'counties_in_directory': counties, 'jails_in_directory': jails,
            'jails_with_real_website': jails_real_site, 'jails_active_flag': jails_active,
            'registered': registered, 'enabled': enabled, 'verified': verified,
            'staging_only': staging, 'counties_with_source': counties_with_source,
            'ingesting_last_7d': ingesting_7d, 'ran_last_7d': ran_7d, 'records_total': records,
            'records_public': public_records,
            'jurisdictions_with_records': jurisdictions_with_records,
            'coverage_pct_of_jails': round(100.0 * ingesting_7d / jails, 2) if jails else 0.0,
            'files': stub_counts(), 'states': states}


def render_text(d: dict) -> str:
    f = d['files']
    lines = [
        'JailMap — national coverage (truth, not scaffolding)',
        '=' * 58,
        f"  Jails in directory                 {d['jails_in_directory']:>6}",
        f"    ...with a real jurisdiction site {d['jails_with_real_website']:>6}",
        f"  Counties in directory              {d['counties_in_directory']:>6}",
        f"  Registered jurisdictions           {d['registered']:>6}",
        f"  Enabled for ingestion              {d['enabled']:>6}",
        f"  Ingesting in the last 7 days       {d['ingesting_last_7d']:>6}   <-- the real number",
        f"    (of {d['ran_last_7d']} that ran at all)",
        f"  Coverage of jails                  {d['coverage_pct_of_jails']:>5}%",
        '',
        f"  Booking records                    {d['records_total']:>6}  ({d['records_public']} public)",
        '',
        'Scaffolding (NOT coverage)',
        '-' * 58,
        f"  county adapter.py files            {f['county_adapter_files']:>6}",
        f"    ...raising NotImplementedError   {f['county_adapter_stubs']:>6}",
        f"    ...with real code                {f['county_adapters_real']:>6}",
        f"  backend/adapters files             {f['backend_adapter_files']:>6}",
        '',
        'By state (top 15 by ingestion)',
        '-' * 58,
        f"  {'ST':<4}{'counties':>9}{'jails':>7}{'reg':>6}{'enabled':>9}{'live7d':>8}{'records':>9}",
    ]
    for row in d['states'][:15]:
        if row['registered'] or row['jails']:
            lines.append(f"  {row['state']:<4}{row['counties']:>9}{row['jails']:>7}"
                         f"{row['registered']:>6}{row['enabled']:>9}{row['ingesting_7d']:>8}"
                         f"{row['records']:>9}")
    active = [s for s in d['states'] if s['ingesting_7d']]
    lines += ['', f"  States with any live ingestion: {len(active)} of {len(d['states'])}"]
    return '\n'.join(lines)


def render_markdown(d: dict) -> str:
    f = d['files']
    out = [
        '# JailMap coverage baseline', '',
        f"Generated by `scripts/national/audit_coverage.py`.", '',
        '| Metric | Value |', '|---|---|',
        f"| Jails in directory | {d['jails_in_directory']:,} |",
        f"| Jails with a real jurisdiction site | {d['jails_with_real_website']:,} |",
        f"| Counties in directory | {d['counties_in_directory']:,} |",
        f"| Registered jurisdictions | {d['registered']:,} |",
        f"| Enabled for ingestion | {d['enabled']:,} |",
        f"| **Ingesting in the last 7 days** | **{d['ingesting_last_7d']:,}** |",
        f"| Coverage of jails | {d['coverage_pct_of_jails']}% |",
        f"| Booking records | {d['records_total']:,} ({d['records_public']:,} public) |",
        '', '## Scaffolding — not coverage', '',
        '| Metric | Value |', '|---|---|',
        f"| `states/**/adapter.py` files | {f['county_adapter_files']:,} |",
        f"| …raising `NotImplementedError` | {f['county_adapter_stubs']:,} |",
        f"| …with real code | {f['county_adapters_real']:,} |",
        f"| `backend/adapters/` files | {f['backend_adapter_files']:,} |",
        '', '## By state', '',
        '| State | Counties | Jails | Registered | Enabled | Live (7d) | Records |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for row in d['states']:
        if row['registered'] or row['ingesting_7d']:
            out.append(f"| {row['state']} | {row['counties']:,} | {row['jails']:,} | "
                       f"{row['registered']:,} | {row['enabled']:,} | {row['ingesting_7d']:,} | "
                       f"{row['records']:,} |")
    return '\n'.join(out) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='JailMap national coverage audit')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--json', action='store_true', help='emit JSON')
    group.add_argument('--markdown', action='store_true', help='emit markdown')
    parser.add_argument('--out', help='write output to this path')
    args = parser.parse_args()

    try:
        data = audit()
    except KeyError:
        print('DATABASE_URL is not set — run via scripts/national/run.sh', file=sys.stderr)
        return 2
    except Exception as error:  # psycopg errors, connection refused, etc.
        print(f'audit failed: {type(error).__name__}: {error}', file=sys.stderr)
        return 2

    if args.json:
        text = json.dumps(data, indent=2, default=str)
    elif args.markdown:
        text = render_markdown(data)
    else:
        text = render_text(data)

    if args.out:
        Path(args.out).write_text(text)
        print(f'wrote {args.out}')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
