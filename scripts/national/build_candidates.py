#!/usr/bin/env python3
"""Build the national candidate list for the source census.

Normalises every research catalog in `data/` into one file the census can consume
(`state,county,jail,url`), deduplicates, and — critically — separates OFFICIAL
sources from third-party aggregators.

MISSION.md: "Never use a third-party mirror as an authority." Catalogs assembled by
earlier passes contain aggregator URLs (currentprisonlist.com and friends) sitting
in the same column as real sheriff domains. Feeding those to the census unfiltered
would produce a vendor histogram built partly on mirrors.

Three outputs:
  candidates-national.csv    official + unknown hosts, ready to probe
  candidates-thirdparty.csv  aggregators, retained for reference, NOT probed
  candidates-backlog.csv     rows with no URL at all — the discovery backlog

Run via scripts/national/run.sh build_candidates.py
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

# Catalogs to consume, newest/most-authoritative first. Later files do not
# overwrite an earlier curated name for the same (state, county, url).
CATALOGS = [
    'official-jail-source-leads.csv',
    'official-sources-only.csv',
    'us-jail-research-catalog.csv',
    'al-research-catalog.csv',
    'fl-county-roster-urls.csv',
    'idaho-jail-sources.csv',
    'sd-jail-sources.csv',
]
# NOTE: national/source-census.csv is an OUTPUT of the census tool, never an input.
# Listing it here created a feedback loop that fed probe results back in as if they
# were researched sources.

# Known third-party aggregators / mirrors. Not authorities under MISSION.md.
THIRD_PARTY = (
    'currentprisonlist', 'inmatesearch', 'jailinmatesearch', 'mugshots.com',
    'mugshot', 'bustedmugshots', 'arrest.org', 'arrests.org', 'jailbase',
    'inmateaid', 'inmatelocator', 'prisonroster', 'whoisjail', 'jailroster',
    'inmate-lookup', 'inmatelookup', 'publicrecords', 'recordsfinder',
    'staterecords', 'backgroundcheck', 'truthfinder', 'spokeo', 'beenverified',
    'peoplefinders', 'fastpeoplesearch', 'whitepages', 'radaris', 'neighborswho',
    'opencorporates', 'jailguide', 'inmatesplus', 'cityjail', 'countyjail',
)

OFFICIAL_SUFFIXES = ('.gov', '.us', '.mil')

# Sentinel order for candidate ranking: a sheriff's own domain is far more likely
# to expose a roster than a county commission homepage.
SHERIFF_RE = re.compile(r'sheriff|countyso|\bso\b', re.I)

DOTGOV_FILE = 'national/dotgov-full.csv'


def stripped_domain_core(domain: str) -> str:
    """'calhounalsheriff.gov' -> 'calhounalsheriff'"""
    host = domain.strip().lower()
    for suffix in ('.gov', '.us', '.mil'):
        if host.endswith(suffix):
            host = host[: -len(suffix)]
            break
    return re.sub(r'[^a-z0-9]', '', host)


def county_slug(name: str) -> str:
    base = re.sub(r'\s+County$', '', (name or '').strip(), flags=re.I)
    return re.sub(r'[^a-z0-9]', '', base.lower())


def org_county_slug(org: str) -> str:
    """Extract the county from an organisation name, precisely.

    'Lee County Arkansas Sheriff' -> 'lee'   (NOT 'arkansas')
    Parsing the word(s) before the first 'County' is what prevents the org-name
    substring false positive that assigned leesheriffar.gov to Arkansas County.
    """
    match = re.search(r'([A-Za-z][A-Za-z .\'\-]*?)\s+County\b', org or '', re.I)
    if not match:
        return ''
    return re.sub(r'[^a-z0-9]', '', match.group(1).lower())


def domain_matches(domain_core: str, slug: str) -> bool:
    """Token-aware match, deliberately strict.

    Only an exact match or a county-name PREFIX is accepted, plus an explicit
    'countyof'-style prefix. Loose `endswith`/contains matching was removed after
    it assigned `18wjdarkansas.gov` (18th West Judicial District) and
    `almaarkansas.gov` (City of Alma) to Arkansas County — because 'arkansas' is
    also the state name. A wrong source is worse than a missing one: unmatched
    counties fall to the review pile, where a human decides.
    """
    if not slug or not domain_core:
        return False
    if domain_core == slug or domain_core.startswith(slug):
        return True
    for prefix in ('countyof', 'cityof', 'citycountyof', 'county'):
        if domain_core.startswith(prefix) and domain_core[len(prefix):].startswith(slug):
            return True
    return False


def resolves(host: str, timeout: float = 3.0) -> bool:
    """Does this hostname resolve at all?

    The CISA .gov registry lists REGISTERED domains, not live ones. In the first
    national pass, 42% of sheriff candidates were NXDOMAIN — agencies register a
    domain defensively and deploy a site years later. Verified against a public
    resolver (dig @1.1.1.1) to be real, not a local DNS fault. Filtering on this
    before probing avoids spending requests on hosts that cannot answer, and keeps
    the reachable-coverage denominator honest.
    """
    import socket
    previous = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(host, 443)
        return True
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(previous)


def dns_filter(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split candidates into (resolving, dead) using a bounded thread pool."""
    from concurrent.futures import ThreadPoolExecutor
    unique_hosts = sorted({urlsplit(c['url']).hostname or '' for c in candidates})
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = dict(zip(unique_hosts, pool.map(resolves, unique_hosts)))
    live = [c for c in candidates if results.get(urlsplit(c['url']).hostname or '', False)]
    dead = [c for c in candidates if not results.get(urlsplit(c['url']).hostname or '', False)]
    return live, dead


def load_counties():
    """The 3,143-row national county directory, as (state_abbrev, state_name, county_name)."""
    import psycopg
    with psycopg.connect(os.environ['DATABASE_URL']) as connection:
        rows = connection.execute('''SELECT s.abbrev, s.name, c.name
            FROM "County" c JOIN "State" s ON s.id=c."stateId"
            ORDER BY s.abbrev, c.name''').fetchall()
    return [(str(r[0]).strip(), str(r[1]).strip(), str(r[2]).strip()) for r in rows]


def match_dotgov(counties, registry):
    """Join counties to the CISA .gov registry.

    Returns (candidates, ambiguous, unmatched). A county may yield several domains;
    each is ranked 1 for sheriff/sheriff's-office sites, 2 otherwise.
    """
    by_state: dict[str, list] = defaultdict(list)
    for row in registry:
        state = (row.get('State') or '').strip().upper()
        domain = (row.get('Domain name') or '').strip().lower()
        if state and domain:
            by_state[state].append({
                'domain': domain,
                'org': (row.get('Organization name') or '').strip(),
                'city': (row.get('City') or '').strip(),
                'core': stripped_domain_core(domain),
            })

    candidates, ambiguous, unmatched = [], [], []
    for state, state_name, name in counties:
        slug = county_slug(name)
        if not slug:
            continue
        # When the county is named after its own state (Arkansas County AR,
        # Washington County WA, ...), domain matching cannot tell the county site
        # from the state site — 'arkansas.gov' and 'arkansas529.gov' both matched
        # Arkansas County. Require an organisation that literally says
        # "<Name> County" instead of guessing from the domain.
        name_collides_with_state = slug == county_slug(state_name)
        hits = []
        for entry in by_state.get(state, []):
            if not name_collides_with_state and domain_matches(entry['core'], slug):
                hits.append((entry, 'domain'))
            elif org_county_slug(entry['org']) == slug:
                hits.append((entry, 'organization'))
        if not hits:
            unmatched.append((state, name))
            continue
        # Deduplicate by domain, keeping the strongest match basis.
        seen: dict[str, tuple] = {}
        for entry, basis in hits:
            if entry['domain'] not in seen or basis == 'domain':
                seen[entry['domain']] = (entry, basis)
        ranked = []
        for entry, basis in seen.values():
            is_sheriff = bool(SHERIFF_RE.search(entry['domain']) or SHERIFF_RE.search(entry['org']))
            ranked.append({
                'state': state,
                'county': name,
                'jail': f"{name} — {'sheriff site' if is_sheriff else 'county site'}",
                'url': f"https://{entry['domain']}/",
                'rank': 1 if is_sheriff else 2,
                'match_basis': basis,
                'org': entry['org'],
            })
        ranked.sort(key=lambda r: (r['rank'], r['url']))
        candidates.extend(ranked)
        if len(seen) > 1 or any(r['match_basis'] == 'organization' for r in ranked):
            ambiguous.append({'state': state, 'county': name, 'domains': sorted(seen)})
    return candidates, ambiguous, unmatched


def host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or '').lower()
    except ValueError:
        return ''


def classify_host(host: str) -> str:
    """official | thirdparty | unknown. Deliberately conservative: anything not
    clearly a government domain is 'unknown' and still needs human review."""
    if not host:
        return 'none'
    if any(bad in host for bad in THIRD_PARTY):
        return 'thirdparty'
    if host.endswith(OFFICIAL_SUFFIXES):
        return 'official'
    # County/sheriff domains on private TLDs are common and legitimate, but we do
    # not guess: leave them for review rather than asserting authority.
    if re.search(r'(^|\.)(co|ci|county|sheriff|so|pd)[.-]', host) or 'sheriff' in host:
        return 'unknown'
    return 'unknown'


ALIASES = {
    'state': 'state', 'st': 'state', 'state_abbrev': 'state', 'abbrev': 'state',
    'county': 'county', 'county_name': 'county',
    'facility': 'jail', 'jail': 'jail', 'facility_name': 'jail', 'name': 'jail',
    'url': 'url', 'source_url': 'url', 'website': 'url', 'candidate_url': 'url',
    'access_status': 'access', 'status': 'access', 'access': 'access',
}


def normalise_row(raw: dict, default_state: str) -> dict:
    row: dict[str, str] = {}
    for key, value in raw.items():
        if not key:
            continue
        target = ALIASES.get(key.strip().lower())
        if target and value is not None:
            row[target] = str(value).strip()
    row.setdefault('state', default_state)
    return row


def state_from_filename(path: Path) -> str:
    """fl-county-roster-urls.csv -> FL (the FL catalog has no state column)."""
    match = re.match(r'([a-z]{2})[-_]', path.name)
    return match.group(1).upper() if match else ''


def county_display(county: str) -> str:
    text = (county or '').strip()
    if not text:
        return ''
    return text if text.lower().endswith('county') else f'{text} County'


def main() -> int:
    parser = argparse.ArgumentParser(description='Build national candidate list from research catalogs')
    parser.add_argument('--data-dir', default='/src/data')
    parser.add_argument('--sample', type=int, default=0, help='cap official+unknown output (0 = all)')
    parser.add_argument('--dotgov-file', default=None,
                        help=f'CISA .gov registry CSV (default <data-dir>/{DOTGOV_FILE})')
    parser.add_argument('--skip-catalogs', action='store_true',
                        help='only process the .gov registry')
    parser.add_argument('--max-per-county', type=int, default=2,
                        help='registry domains to keep per county, sheriff first (0 = all)')
    parser.add_argument('--dns-check', action='store_true',
                        help='drop .gov candidates whose hostname does not resolve')
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    rows: dict[tuple, dict] = {}
    backlog: list[dict] = []
    thirdparty: list[dict] = []
    sources_used = []

    for name in CATALOGS:
        if args.skip_catalogs:
            break
        path = data_dir / name
        if not path.exists():
            continue
        sources_used.append(name)
        default_state = state_from_filename(path)
        with path.open(newline='', errors='ignore') as handle:
            for raw in csv.DictReader(handle):
                row = normalise_row(raw, default_state)
                url = row.get('url', '')
                state = (row.get('state') or '').upper()[:2]
                county = row.get('county', '')
                jail = row.get('jail', '')
                if not url:
                    # Only the explicit research catalogs contribute backlog rows.
                    if row.get('access') == 'no_public_source' or name.endswith('research-catalog.csv'):
                        backlog.append({'state': state, 'county': county, 'jail': jail,
                                        'origin': name, 'access': row.get('access', '')})
                    continue
                if not state:
                    continue
                host = host_of(url)
                kind = classify_host(host)
                record = {'state': state, 'county': county, 'jail': jail, 'url': url,
                          'host': host, 'origin': name, 'official_guess': kind}
                if kind == 'thirdparty':
                    thirdparty.append(record)
                    continue
                key = (state, county.lower(), url.rstrip('/'))
                rows.setdefault(key, record)

    official = [r for r in rows.values() if r['official_guess'] == 'official']
    unknown = [r for r in rows.values() if r['official_guess'] == 'unknown']
    ordered = sorted(official + unknown, key=lambda r: (r['state'], r['county']))
    if args.sample:
        ordered = ordered[:args.sample]

    out_dir = data_dir / 'national'
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = ['state', 'county', 'jail', 'url']

    def write(path: Path, items: list[dict]) -> None:
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for item in items:
                writer.writerow({**item, 'county': county_display(item.get('county', ''))})

    write(out_dir / 'candidates-national.csv', ordered)
    with (out_dir / 'candidates-thirdparty.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['state', 'county', 'jail', 'host', 'url', 'origin'],
                                extrasaction='ignore')
        writer.writeheader()
        for item in thirdparty:
            writer.writerow({**item, 'county': county_display(item.get('county', ''))})
    with (out_dir / 'candidates-backlog.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['state', 'county', 'jail', 'origin', 'access'])
        writer.writeheader()
        for item in backlog:
            writer.writerow({**item, 'county': county_display(item.get('county', ''))})

    print(f'Catalogs read: {len(sources_used)}')
    for name in sources_used:
        print(f'  - {name}')
    print()
    print(f'  official hosts            {len(official):>5}')
    print(f'  unknown hosts (review)    {len(unknown):>5}')
    print(f'  THIRD-PARTY (excluded)    {len(thirdparty):>5}   <- never an authority')
    print(f'  no URL (discovery backlog){len(backlog):>5}')
    print(f'  -> probe list             {len(ordered):>5}')
    print()
    if ordered:
        print('By state (probe list)')
        per = Counter(r['state'] for r in ordered)
        for state, count in per.most_common(20):
            print(f'  {state:<4}{count:>5}')
        hosts = {r['host'] for r in ordered}
        print(f'\nUnique hosts in probe list: {len(hosts)}')
        print(f'Suggested runtime at 1 req/sec/host (no follow): ~{len(ordered)} requests')
    if thirdparty:
        print('\nTop excluded third-party hosts (kept in candidates-thirdparty.csv):')
        for host, count in Counter(r['host'] for r in thirdparty).most_common(10):
            print(f'  {host:<44}{count:>4}')

    # --- CISA .gov registry: authoritative county -> domain mapping ------------
    registry_path = Path(args.dotgov_file) if args.dotgov_file else (data_dir / DOTGOV_FILE)
    if not registry_path.exists():
        print(f'\n.gov registry not found at {registry_path} — skipping.')
        print('Fetch it with:')
        print(f'  curl -o data/national/dotgov-full.csv \\')
        print('    https://raw.githubusercontent.com/cisagov/dotgov-data/main/current-full.csv')
        return 0

    with registry_path.open(newline='', errors='ignore') as handle:
        registry = list(csv.DictReader(handle))
    counties = load_counties()
    matched, ambiguous, unmatched = match_dotgov(counties, registry)

    if args.max_per_county:
        kept, per_county = [], Counter()
        for row in matched:
            key = (row['state'], row['county'])
            if per_county[key] < args.max_per_county:
                kept.append(row)
                per_county[key] += 1
        matched = kept

    if args.dns_check:
        before = len(matched)
        matched, dead = dns_filter(matched)
        with (out_dir / 'dotgov-dead.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['state', 'county', 'jail', 'url'],
                                    extrasaction='ignore')
            writer.writeheader()
            for row in dead:
                writer.writerow(row)
        print(f'\n  DNS check: {before} -> {len(matched)} resolving '
              f'({len(dead)} NXDOMAIN -> dotgov-dead.csv)')

    with (out_dir / 'candidates-dotgov.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['state', 'county', 'jail', 'url',
                                                   'rank', 'match_basis', 'org'])
        writer.writeheader()
        for row in sorted(matched, key=lambda r: (r['state'], r['county'], r['rank'])):
            writer.writerow(row)

    with (out_dir / 'dotgov-ambiguous.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['state', 'county', 'domains'])
        writer.writeheader()
        for row in ambiguous:
            writer.writerow({**row, 'domains': ';'.join(row['domains'])})

    sheriff = sum(1 for r in matched if r['rank'] == 1)
    counties_covered = {(r['state'], r['county']) for r in matched}
    print(f'\n=== CISA .gov registry join ===')
    print(f'  registry rows           {len(registry):>6}')
    print(f'  counties queried        {len(counties):>6}')
    print(f'  counties matched        {len(counties_covered):>6}'
          f'  ({100.0*len(counties_covered)/max(1,len(counties)):.1f}%)')
    print(f'  unmatched counties      {len(unmatched):>6}')
    print(f'  candidate domains       {len(matched):>6}')
    print(f'    rank 1 (sheriff/SO)   {sheriff:>6}   <- probe these first')
    print(f'    rank 2 (county site)  {len(matched)-sheriff:>6}')
    print(f'  ambiguous for review    {len(ambiguous):>6}  -> dotgov-ambiguous.csv')
    print(f'  -> candidates-dotgov.csv')
    print('\n  rank-1 sample:')
    for row in [r for r in matched if r['rank'] == 1][:10]:
        print(f"    {row['state']} {row['county']:<24} {row['url']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
