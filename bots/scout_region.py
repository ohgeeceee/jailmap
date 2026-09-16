#!/usr/bin/env python3
"""source-scout-<region>: rank uncovered counties into an actionable worklist.

Read-only. It does NOT invent hostnames and does NOT write source leads: a lead
needs evidence plus human review. This bot answers "what should we discover next
in this region" with the counties that have no enabled source, ordered by how
many facilities the directory holds, and flags which already carry a lead.
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jailmap_bots as jb

REGIONS = {
    'west': ['AK', 'AZ', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'NM', 'OR', 'UT', 'WA', 'WY'],
    'south': ['AL', 'AR', 'FL', 'GA', 'KY', 'LA', 'MS', 'NC', 'OK', 'SC', 'TN', 'TX', 'VA', 'WV'],
    'north': ['CT', 'DE', 'IA', 'IL', 'IN', 'KS', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'ND', 'NE',
              'NH', 'NJ', 'NY', 'OH', 'PA', 'RI', 'SD', 'VT', 'WI'],
}

UNCOVERED = ('SELECT s.abbrev, c.name, count(j.id) AS jails '
             'FROM "County" c '
             'JOIN "State" s ON s.id = c."stateId" '
             'LEFT JOIN "Jail" j ON j."countyId" = c.id '
             'LEFT JOIN (SELECT county_id::text AS cid, bool_or(enabled) AS enabled '
             'FROM records.jurisdictions WHERE county_id IS NOT NULL GROUP BY 1) src '
             'ON src.cid = c.id::text '
             'WHERE s.abbrev IN (%s) AND coalesce(src.enabled, false) = false '
             'GROUP BY 1, 2 ORDER BY jails DESC, c.name LIMIT %d')

TOTAL = ('SELECT count(1) FROM "County" c '
         'JOIN "State" s ON s.id = c."stateId" '
         'LEFT JOIN (SELECT county_id::text AS cid, bool_or(enabled) AS enabled '
         'FROM records.jurisdictions WHERE county_id IS NOT NULL GROUP BY 1) src '
         'ON src.cid = c.id::text '
         'WHERE s.abbrev IN (%s) AND coalesce(src.enabled, false) = false')


def leads_by_state_county():
    found = set()
    path = os.path.join(jb.ROOT, 'data', 'official-jail-source-leads.csv')
    try:
        with open(path, newline='', encoding='utf-8') as handle:
            for row in csv.DictReader(handle):
                state = (row.get('state') or '').strip().upper()
                county = (row.get('county') or '').strip().lower()
                if state and county:
                    found.add((state, county))
    except (OSError, csv.Error, AttributeError):
        pass
    return found


def build(region, limit):
    states = REGIONS[region]
    listed = ','.join("'%s'" % s for s in states)
    leads = leads_by_state_county()
    rows = []
    for line in jb.query(UNCOVERED % (listed, limit)):
        parts = line.split('|')
        if len(parts) < 3:
            continue
        state, county, jails = parts[0], parts[1], parts[2]
        rows.append([state, county, jails, 'yes' if (state, county.lower()) in leads else 'no'])
    total = jb.query(TOTAL % listed)
    body = jb.header('source-scout-%s' % region, '%s region worklist' % region.title(),
                     'Green tier: reads the directory and writes this digest only. It records no '
                     'lead, enables no source, and fetches nothing.')
    body += '\n- Counties in this region with no enabled source: **%s**\n' % (total[0] if total else 'unknown')
    body += '- Showing the top %d, busiest first (facility count in the directory)\n' % limit
    body += ('- Of the shown rows, already carrying a lead: %d\n\n'
             % sum(1 for row in rows if row[3] == 'yes'))
    body += jb.table(rows, ['State', 'County', 'Facilities', 'Has lead'])
    body += ('\n## Next action\n\nFor each row with no lead: locate the official roster or custody '
             'page, then add an evidence-backed, **disabled** lead to '
             '`data/official-jail-source-leads.csv`. Do not guess hostnames - the rollout plan '
             'measured that `<county>countysheriff.com` almost never resolves, and a third-party '
             'mirror is never an authority.\n')
    return body, len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('region', choices=sorted(REGIONS))
    parser.add_argument('--limit', type=int, default=40)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    body, count = build(args.region, max(1, min(500, args.limit)))
    if args.write:
        path = jb.write_digest('source-scout-%s' % args.region, 'worklist', body)
        print('source-scout-%s: wrote %s (%d target rows)' % (args.region, path, count))
    else:
        print(body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
