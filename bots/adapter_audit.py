#!/usr/bin/env python3
"""feed-builder: audit adapter registration and draft the registration plan.

Read-only. Counts what exists in backend/adapters/, what backend/ingest.py
registers, and which modules look like real code versus scaffolding - then drafts
the registration candidate list for a human to act on. It never edits ingest.py.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jailmap_bots as jb

ADAPTERS_DIR = os.path.join(jb.ROOT, 'backend', 'adapters')
INGEST = os.path.join(jb.ROOT, 'backend', 'ingest.py')


def registered_keys():
    try:
        with open(INGEST, encoding='utf-8') as handle:
            text = handle.read()
    except OSError:
        return set(), 'ingest.py unreadable'
    start = text.find('ADAPTERS')
    if start < 0:
        return set(), 'no ADAPTERS dict found'
    end = text.find('\n}', start)
    block = text[start:end if end > 0 else len(text)]
    keys = set(re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]\s*:", block))
    return keys, 'ADAPTERS dict found at offset %d' % start


def modules():
    out = {}
    try:
        names = sorted(os.listdir(ADAPTERS_DIR))
    except OSError:
        return out
    for name in names:
        if not name.endswith('.py') or name == '__init__.py':
            continue
        try:
            with open(os.path.join(ADAPTERS_DIR, name), encoding='utf-8') as handle:
                text = handle.read()
        except OSError:
            continue
        out[name[:-3]] = {
            'lines': text.count('\n') + 1,
            'scaffold': 'NotImplementedError' in text,
            'has_entry': bool(re.search(r'def\s+(fetch|parse|rows|adapt|run|collect)', text)),
        }
    return out


def build():
    keys, note = registered_keys()
    mods = modules()
    real = {name: meta for name, meta in mods.items() if not meta['scaffold']}
    orphaned = sorted(name for name in real if name not in keys)
    scaffolding = sorted(name for name, meta in mods.items() if meta['scaffold'])
    nameless = sorted(name for name, meta in real.items() if not meta['has_entry'])

    body = jb.header('feed-builder', 'adapter registration audit',
                     'Green tier: reads the repository and writes this digest only. It does not '
                     'edit `backend/ingest.py`, run ingestion, or change any source.')
    body += '\n- Adapter modules present: **%d**\n' % len(mods)
    body += '- Registered in `ingest.py`: **%d** (%s)\n' % (len(keys), note)
    body += '- Without `NotImplementedError`: **%d**\n' % len(real)
    body += '- **Orphaned (real module, not registered): %d**\n' % len(orphaned)
    body += '- Scaffolding modules raising `NotImplementedError`: %d\n' % len(scaffolding)
    body += '- Real modules with no fetch/parse entry point: %d\n\n' % len(nameless)
    body += '## Registration candidates (orphaned)\n\n'
    body += jb.table([[name, real[name]['lines'], 'yes' if real[name]['has_entry'] else 'no']
                      for name in orphaned], ['Module', 'Lines', 'Entry point'])
    body += ('\nA candidate still needs a dry run against a live source before registration. The '
             'registry key must match the value a jurisdiction row uses in '
             '`records.jurisdictions.adapter`.\n')
    if scaffolding:
        body += '\n## Scaffolding - never count as coverage\n\n'
        body += jb.table([[name, mods[name]['lines']] for name in scaffolding[:40]], ['Module', 'Lines'])
        body += ('\n`docs/coverage-baseline.md` records the same trap: 2,947 of 2,978 state adapter '
                 'files raise `NotImplementedError`. Any dashboard reporting them as coverage is '
                 'misreporting the product to its own operator.\n')
    body += ('\n## Next action\n\nDraft a registration diff for the orphaned modules that still target '
             'live sources, each with a dry-run transcript, and hand it over as a Red-tier draft for '
             'human approval. Never register blind.\n')
    return body, {'orphaned': len(orphaned), 'registered': len(keys), 'modules': len(mods)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    body, stats = build()
    if args.write:
        path = jb.write_digest('feed-builder', 'adapter-audit', body)
        print('feed-builder: wrote %s (%d orphaned, %d registered, %d modules)'
              % (path, stats['orphaned'], stats['registered'], stats['modules']))
    else:
        print(body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
