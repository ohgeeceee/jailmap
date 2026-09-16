#!/usr/bin/env python3
"""privacy-reviewer: render a verdict on every registered source.

Read-only. Applies the review checklist from MISSION.md mechanically, so the
operator gets a verdict per source instead of an opinion: is this source legally
referenced, reviewed, structurally capable of returning a roster, and safe to
carry? It changes nothing and enables nothing.
"""
import argparse
import os
import sys
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jailmap_bots as jb

ROSTER_HINTS = ('roster', 'inmate', 'custody', 'booking', 'jail', 'detention', 'search',
                'inmates', 'offender', 'current', 'population', 'blotter', 'arrest')

SOURCES = ('SELECT id::text, state, county, facility_name, enabled::text, review_status, '
           'staging_only::text, coalesce(source_url, \'\'), coalesce(authorization_reference, \'\'), '
           'adapter FROM records.jurisdictions ORDER BY enabled DESC, state, county')


def looks_like_homepage(url):
    try:
        parsed = urlsplit(url)
    except ValueError:
        return True
    path = (parsed.path or '').strip('/')
    if not path:
        return True
    return not any(hint in path.lower() for hint in ROSTER_HINTS)


def verdict_for(row):
    (state, county, facility, enabled, review, staging, url, authorization, adapter) = row
    enabled = enabled == 'true'
    staging = staging == 'true'
    weak_auth = authorization.strip().lower() in ('', 'pending', 'none', 'unknown')
    verified = review.strip().lower() == 'verified'
    if enabled and not verified:
        return 'BLOCKED', 'enabled while review_status=%s' % (review or 'empty')
    if enabled and weak_auth:
        return 'BLOCKED', 'enabled with no authorization reference (%s)' % (authorization or 'empty')
    if enabled and looks_like_homepage(url) and adapter == 'standard_json':
        return 'BLOCKED', 'source_url is a homepage for a standard_json adapter - cannot return a roster'
    if verified and not weak_auth and not looks_like_homepage(url):
        if enabled:
            return 'READY_FOR_ADAPTER', 'enabled, reviewed, referenced; monitor freshness'
        return 'READY_FOR_ADAPTER', 'reviewed and referenced; awaiting a staging dry run'
    if looks_like_homepage(url):
        return 'NEEDS_REVIEW', 'source_url does not look like a roster page'
    if enabled and staging:
        return 'READY_FOR_ADAPTER', 'staging-only; confirm adult eligibility before public enablement'
    return 'NEEDS_REVIEW', 'manual review'


def build():
    rows, counts = [], {}
    enabled_total = enabled_capable = 0
    for line in jb.query(SOURCES):
        parts = line.split('|')
        if len(parts) < 10:
            continue
        state, county, facility, enabled, review, staging, url, authorization, adapter = parts[1:10]
        verdict, reason = verdict_for(parts[1:10])
        counts[verdict] = counts.get(verdict, 0) + 1
        if enabled == 'true':
            enabled_total += 1
            if verdict == 'READY_FOR_ADAPTER':
                enabled_capable += 1
        rows.append(['%s/%s' % (state, county), facility[:38], adapter[:18], enabled,
                     verdict, reason[:70]])

    body = jb.header('privacy-reviewer', 'source verdicts',
                     'Green tier: read-only review. A verdict is an opinion, not an action - '
                     'nothing here enables a source, flips staging_only, or publishes.')
    body += '\n- Registered sources reviewed: **%d**\n' % len(rows)
    body += '- Verdicts: ' + ', '.join('%s %d' % (k, v) for k, v in sorted(counts.items())) + '\n'
    body += ('- Enabled sources: **%d**, of which carrying a clean verdict: **%d**\n'
             % (enabled_total, enabled_capable))
    body += ('\nCoverage claims only equal capability when those two numbers match. A gap here means '
             '"enabled" overstates what the product can deliver.\n\n')
    body += jb.table(rows, ['Location', 'Facility', 'Adapter', 'Enabled', 'Verdict', 'Reason'])
    body += ('\n## Next action\n\nEvery BLOCKED row is a Red-tier remediation candidate: draft the '
             'disable, with its reason, and let a human approve it. Never disable in a batch without '
             'that record.\n')
    return body, counts, enabled_total, enabled_capable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    body, counts, enabled_total, capable = build()
    if args.write:
        path = jb.write_digest('privacy-reviewer', 'verdicts', body)
        print('privacy-reviewer: wrote %s (%s; enabled %d, clean %d)'
              % (path, counts, enabled_total, capable))
    else:
        print(body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
