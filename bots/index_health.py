#!/usr/bin/env python3
"""search-indexer: report search index and outbox health.

Read-only. Checks the Meilisearch instance, the hydration outbox lag against the
records it is meant to carry, and whether anything is stuck. It repairs nothing:
a repair is a production action and belongs behind the human gate.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jailmap_bots as jb

MEILI = os.environ.get('MEILI_URL', 'http://127.0.0.1:7700')

OUTBOX_TOTAL = 'SELECT count(1), coalesce(max(queued_at)::text, \'\') FROM records.search_outbox'
OUTBOX_LAG = ('SELECT count(1) FROM records.search_outbox o JOIN records.inmates i ON i.id = o.inmate_id '
              'WHERE o.version <> i.version')
PUBLIC_RECORDS = 'SELECT count(1) FROM records.inmates WHERE visibility = \'public\''


def get_json(url, timeout=6):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, OSError, ValueError):
        return None, None


def build():
    health_status, health = get_json(MEILI + '/health')
    indexes_status, indexes = get_json(MEILI + '/indexes')
    outbox = jb.query(OUTBOX_TOTAL)
    lag = jb.query(OUTBOX_LAG)
    public = jb.query(PUBLIC_RECORDS)

    body = jb.header('search-indexer', 'index and outbox health',
                     'Green tier: read-only checks. It repairs nothing - index or hydration changes '
                     'are production actions and wait for a human.')
    body += '\n| Check | Result |\n|---|---|\n'
    body += '| Meilisearch /health | %s |\n' % ('%s %s' % (health_status, health or '') if health_status else 'unreachable')
    if indexes_status == 200 and isinstance(indexes, dict):
        results = indexes.get('results', [])
        summary = ', '.join('%s=%s docs' % (item.get('uid'), item.get('numberOfDocuments'))
                            for item in results[:8]) or 'no indexes'
        body += '| Meilisearch indexes | %s |\n' % summary
    elif indexes_status:
        body += '| Meilisearch indexes | HTTP %s (auth required or unavailable) |\n' % indexes_status
    else:
        body += '| Meilisearch indexes | unreachable |\n'
    if outbox:
        parts = outbox[0].split('|')
        body += '| Outbox rows | %s |\n' % (parts[0] if parts else '?')
        body += '| Newest outbox entry | %s |\n' % (parts[1] if len(parts) > 1 and parts[1] else 'none')
    body += '| Outbox rows stale vs source version | %s |\n' % (lag[0] if lag else 'unknown')
    body += '| Public records | %s |\n' % (public[0] if public else 'unknown')

    lag_value = lag[0] if lag else 'unknown'
    body += ('\nInterpretation: a rising stale count means published changes are not reaching search. '
             'The outbox is the contract between the records DB and the index; lag is a correctness '
             'bug, not a performance footnote.\n')
    body += ('\n## Next action\n\nIf stale rows are non-zero for two consecutive days, open a Red-tier '
             'draft: what is consuming the outbox, what stalled, and the exact command to drain it.\n')
    return body, lag_value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    body, lag_value = build()
    if args.write:
        path = jb.write_digest('search-indexer', 'index-health', body)
        print('search-indexer: wrote %s (stale outbox rows: %s)' % (path, lag_value))
    else:
        print(body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
