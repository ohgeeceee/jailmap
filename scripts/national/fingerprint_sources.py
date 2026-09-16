#!/usr/bin/env python3
"""JailMap national source census — classify jail websites at directory scale.

Turns the 3,531-row Census landmark directory into a ranked census of candidate
roster sources: who runs a vendor portal, who publishes a table or PDF, who is
gated, and who publishes nothing.

Design constraints (MISSION.md):
  * `robots.txt` is fetched and obeyed for every host before any page fetch.
  * At most one request per host per second, sequential, small concurrency.
  * No captcha solving, no login attempt, no paywall circumvention. A gated site
    is recorded as gated and stops there.
  * Bounded response size and timeout; a slow site is skipped, not hammered.
  * `--dry-run` prints the candidate URLs and exits WITHOUT any network traffic,
    so you can eyeball the plan before anything leaves the VPS.

Run via scripts/national/run.sh fingerprint_sources.py ...
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import urllib.robotparser
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

REPO = Path(os.environ.get('JAILMAP_REPO') or '/src')
USER_AGENT = 'JailMapBot/1.0 (+https://jailmap.com/sources; source discovery)'
TIMEOUT = 12.0
MAX_BYTES = 400_000
HOST_DELAY = 1.0

# --- vendor fingerprint table -------------------------------------------------
# (family, host_needles, body_needles). Host matches are authoritative; body
# matches are advisory only, because corrections pages routinely *mention* other
# systems (VINE victim notification, a linked vendor, marketing text) without
# running them. Matching body-first produced false positives in testing
# (appriss_vine on dcr.hawaii.gov, tyler_odyssey on a Socrata portal).
VENDORS = [
    ('zuercher',           ('zuercherportal.com',), ('zuercher',)),
    ('socrata_open_data',  ('socrata', 'sharefulton', 'opendata'), ('socrata',)),
    ('tyler_jailtracker',  ('jailtracker',), ('jailtracker',)),
    ('tyler_odyssey',      ('odyssey', 'tylertech'), ('tyler technologies',)),
    ('tyler_new_world',    ('newworld',), ('new world systems',)),
    ('appriss_vine',       ('vinelink', 'appriss', 'vinesystem'), ()),
    ('smartweb',           ('smartweb', 'netvision', 'inmatelookup', 'inmate-lookup'), ('netvision',)),
    ('citizenrims',        ('citizenrims',), ('citizenrims',)),
    ('southern_software',  ('southernsoftware',), ('southern software inmate',)),
    ('kimble',             ('kimble',), ()),
    ('guardian',           ('guardiansoftware',), ()),
    ('motorola_spillman',  ('spillman',), ()),
    ('jailinmatesearch',   ('jailinmatesearch',), ()),
]

# Gating indicators. Presence means stop: record it, do not attempt to pass it.
CAPTCHA_MARKERS = ('g-recaptcha', 'hcaptcha', 'cf-chl-', 'turnstile',
                   'are you a human', 'verify you are human', 'just a moment',
                   'checking your browser', 'attention required')
LOGIN_MARKERS = ('type="password"', "type='password'", 'name="password"',
                 'sign in to continue', 'please log in')
ROSTER_KEYWORDS = ('inmate', 'roster', 'booking', 'custody', 'detainee',
                   'current inmates', 'who\'s in jail', 'jail population')

# Classifying `html_roster` on keyword presence alone is badly over-inclusive: it
# labelled every sheriff homepage that merely *mentioned* "inmate". Verified on
# 2026-09-14 — five census-labelled `html_roster` targets contained ZERO tables.
# Now the label requires a real table with an identity column, using the same
# column mapping as the production adapter.
try:
    from backend.adapters.html_roster import (IDENTITY_FIELDS, _TableExtractor,
                                              _map_columns)
    HAVE_TABLE_PARSER = True
except Exception:  # allow the census to run without backend on the path
    HAVE_TABLE_PARSER = False


def roster_tables(body: str) -> tuple[int, int]:
    """(tables carrying an identity column, estimated data rows).

    Zero means this page is not an HTML roster, whatever it mentions.
    """
    if not HAVE_TABLE_PARSER or not body:
        return 0, 0
    extractor = _TableExtractor()
    try:
        extractor.feed(body[:3_000_000])
    except Exception:
        return 0, 0
    tables = rows = 0
    for table in extractor.tables:
        if len(table) < 2:
            continue
        mapping = _map_columns(table[0])
        if not any(field in mapping for field in IDENTITY_FIELDS):
            continue
        tables += 1
        rows += len(table) - 1
    return tables, rows

# Common roster paths to try when a site loads but the homepage has no roster.
# Bounded: at most ROSTER_PROBES extra requests per host, same rate limit.
ROSTER_PATHS = ('/inmate-search', '/inmates', '/inmate', '/jail-roster', '/roster',
                '/jail', '/detention', '/corrections', '/sheriff', '/inmate-lookup',
                '/current-inmates', '/bookings', '/inmate-search.html')
ROSTER_PROBES = 6

# Link discovery. Guessing paths fails: on commission sites `/sheriff` is usually
# a 404, while the real link is `/departments/sheriffs-department`,
# `/31/Sheriffs-Department`, or a different domain entirely (`calcoso.org`,
# `blountalsheriff.org`). Follow the site's own links instead of inventing URLs.
LINK_HINTS = ('sheriff', 'inmate', 'jail', 'roster', 'booking', 'custody',
              'detention', 'corrections', 'arrest', 'offender')
LINKS_TO_TRY = 4
SKIP_LINK_EXT = ('.pdf', '.jpg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.mp4')


def roster_links(body: str, base_url: str) -> list[str]:
    """Anchors on a page that plausibly lead to a roster, best hints first.

    Prefers links whose href or anchor text mentions a roster concept. Returns
    absolute URLs, same-origin links first (cheaper, already robots-checked).
    """
    hrefs = re.findall(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', body, re.I | re.S)
    base_host = urlsplit(base_url).netloc
    scored: list[tuple[int, int, str]] = []
    for href, text in hrefs:
        href = href.strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue
        blob = (href + ' ' + re.sub(r'<[^>]+>', ' ', text)).lower()
        if not any(hint in blob for hint in LINK_HINTS):
            continue
        absolute = urljoin(base_url, href)
        if not absolute.startswith('https://'):
            continue
        if absolute.lower().endswith(SKIP_LINK_EXT):
            continue
        score = sum(1 for hint in LINK_HINTS if hint in blob)
        same_origin = 1 if urlsplit(absolute).netloc == base_host else 0
        scored.append((-score, -same_origin, absolute))
    scored.sort()
    seen, ordered = set(), []
    for _, _, url in scored:
        key = url.rstrip('/')
        if key not in seen:
            seen.add(key)
            ordered.append(url)
    return ordered


def read_input(path: Path) -> list[dict]:
    """Read an explicit candidate list instead of guessing domains.

    Accepts any CSV with state/county/jail/url columns (aliases accepted), so it
    can consume a curated list, a research catalog, or discover_rosters output.
    Domain guessing alone is weak: in the first live sample, 5 of 6 guessed
    hostnames did not resolve.
    """
    aliases = {'url': 'url', 'source_url': 'url', 'website': 'url', 'candidate_url': 'url',
               'state': 'state', 'county': 'county', 'jail': 'jail', 'facility': 'jail',
               'facility_name': 'jail', 'name': 'jail'}
    rows = []
    with path.open(newline='') as handle:
        for raw in csv.DictReader(handle):
            row = {}
            for key, value in raw.items():
                if not key:
                    continue
                target = aliases.get(key.strip().lower())
                if target and value:
                    row[target] = value.strip()
            if row.get('url'):
                rows.append({'state': row.get('state', ''), 'county': row.get('county', ''),
                             'jail': row.get('jail', ''), 'urls': [row['url']]})
    return rows


def connect():
    import psycopg
    return psycopg.connect(os.environ['DATABASE_URL'])


def strip_suffix(name: str) -> str:
    name = name.strip().lower()
    for word in (' county', ' parish', ' borough', ' census area', ' municipality'):
        if name.endswith(word):
            name = name[: -len(word)]
    return re.sub(r'[^a-z0-9]+', '', name)


def candidates(county: str, state: str) -> list[str]:
    """Derive plausible official domains from a county name. Cheap, no search API."""
    slug = strip_suffix(county)
    if not slug:
        return []
    s = state.lower()
    hosts = [
        f'https://www.{slug}countysheriff.com',
        f'https://{slug}countysheriff.com',
        f'https://www.{slug}sheriff.com',
        f'https://{slug}sheriff.com',
        f'https://www.{slug}county{ s }.gov',
        f'https://{slug}county{ s }.gov',
        f'https://co.{slug}.{s}.us',
        f'https://www.{slug}county.gov',
        f'https://{slug}county.gov',
    ]
    seen, out = set(), []
    for host in hosts:
        if host not in seen:
            seen.add(host)
            out.append(host)
    return out


def load_targets(limit: int, states: int, active_only: bool = False) -> list[dict]:
    """Load probe targets.

    NOTE: `"Jail"."isActive"` is true for only 7 of 3,531 rows — those are the
    hand-curated entries. The other 3,524 are Census landmarks bulk-loaded as
    inactive, but they are still real jails and still need a source. Do not
    filter on isActive by default.
    """
    with connect() as connection:
        cur = connection.cursor()
        cur.execute('''SELECT s.abbrev, c.name, j.name
            FROM "Jail" j JOIN "County" c ON c.id=j."countyId"
            JOIN "State" s ON s.id=j."stateId"
            WHERE (NOT %s OR j."isActive")
            ORDER BY s.abbrev, c.name''', (active_only,))
        rows = cur.fetchall()
    by_state: dict[str, list] = defaultdict(list)
    for state, county, jail in rows:
        by_state[state].append({'state': state, 'county': county, 'jail': jail})
    # Round-robin across states so a small sample still spans the country.
    chosen, width = [], 0
    ordered = sorted(by_state)
    if states:
        ordered = ordered[:states]
    while len(chosen) < limit:
        added = False
        for state in ordered:
            bucket = by_state[state]
            if width < len(bucket):
                chosen.append(bucket[width])
                added = True
                if len(chosen) >= limit:
                    break
        if not added:
            break
        width += 1
    return chosen


class Prober:
    """Robots-aware, per-host rate-limited fetcher. Never passes a gate."""

    def __init__(self, respect_robots: bool = True):
        import httpx
        import threading
        self.client = httpx.Client(timeout=TIMEOUT, follow_redirects=True,
                                   headers={'user-agent': USER_AGENT,
                                            'accept': 'text/html,application/xhtml+xml,application/json,application/pdf'})
        self.respect_robots = respect_robots
        self.robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.last_hit: dict[str, float] = {}
        # Politeness is per-host, so concurrency ACROSS hosts is safe. One
        # request per second per host is still enforced exactly, via slot
        # reservation so parallel workers cannot double-hit the same host.
        self._lock = threading.Lock()

    def allowed(self, url: str) -> bool:
        """robots.txt check. Fetched through the same bounded client — the stdlib
        RobotFileParser.read() has no timeout and will hang on a dead host."""
        if not self.respect_robots:
            return True
        parts = urlsplit(url)
        origin = f'{parts.scheme}://{parts.netloc}'
        if origin not in self.robots:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(urljoin(origin, '/robots.txt'))
            self._throttle(parts.netloc)
            try:
                response = self.client.get(urljoin(origin, '/robots.txt'))
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    parser = None  # no usable robots.txt
            except Exception:
                parser = None
            with self._lock:
                self.robots[origin] = parser
        with self._lock:
            parser = self.robots[origin]
        return True if parser is None else parser.can_fetch(USER_AGENT, url)

    def _throttle(self, host: str) -> None:
        """Reserve this host's next allowed slot, then wait for it.

        Reserving under the lock (rather than sleeping while holding it) means N
        parallel workers on the same host still produce exactly one request per
        HOST_DELAY, while workers on different hosts never block each other.
        """
        with self._lock:
            now = time.time()
            nxt = max(now, self.last_hit.get(host, 0.0) + HOST_DELAY)
            self.last_hit[host] = nxt
        delay = nxt - time.time()
        if delay > 0:
            time.sleep(delay)

    def fetch(self, url: str) -> dict:
        if not self.allowed(url):
            return {'status': None, 'error': 'robots_disallowed', 'url': url, 'body': ''}
        self._throttle(urlsplit(url).netloc)
        try:
            with self.client.stream('GET', url) as response:
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        break
                return {'status': response.status_code, 'url': str(response.url),
                        'error': None, 'body': bytes(body).decode('utf-8', 'ignore'),
                        'content_type': response.headers.get('content-type', '')}
        except Exception as error:
            return {'status': None, 'error': type(error).__name__, 'url': url, 'body': ''}


def classify(result: dict) -> tuple[str, str]:
    """Return (vendor_family, access_class)."""
    if result['error'] == 'robots_disallowed':
        return '', 'robots_disallowed'
    if result['error']:
        return '', 'unreachable'
    status = result['status']
    if status in (401, 403, 429):
        return '', 'blocked'
    if status is None or status >= 400:
        return '', f'http_{status}'
    body = result['body'].lower()
    final = result['url'].lower()
    vendor = ''
    for family, host_needles, _ in VENDORS:      # host match: authoritative
        if any(n in final for n in host_needles):
            vendor = family
            break
    if not vendor:
        for family, _, body_needles in VENDORS:  # body match: advisory
            if body_needles and any(n in body for n in body_needles):
                vendor = family
                break
    if any(m in body for m in CAPTCHA_MARKERS):
        return vendor, 'captcha_gated'
    if vendor:
        return vendor, 'vendor_portal'
    if any(m in body for m in LOGIN_MARKERS):
        return vendor, 'login_required'
    if result.get('content_type', '').startswith('application/pdf') or final.endswith('.pdf'):
        return vendor, 'pdf_roster'
    if result.get('content_type', '').startswith('application/json'):
        return vendor, 'json_api'
    # Require real structure, not a keyword mention. `html_roster` means there is a
    # table with an identity column that the production adapter can actually parse.
    tables, _rows = roster_tables(body)
    if tables:
        return vendor, 'html_roster'
    if '<form' in body and any(k in body for k in ROSTER_KEYWORDS):
        return vendor, 'search_form'
    return vendor, 'no_roster_found'


FIELDS = ['probed_at', 'state', 'county', 'jail', 'candidate_url', 'http_status',
          'final_url', 'vendor_family', 'access_class', 'error', 'evidence', 'notes']


def origin_of(url: str) -> str:
    parts = urlsplit(url)
    return f'{parts.scheme}://{parts.netloc}'


def probe_one(prober: Prober, job: dict, follow: bool) -> dict:
    """Probe a jail's candidate URL(s). When the base site loads but has no roster,
    try a bounded set of common roster paths on the same host before giving up —
    a rostered jail usually keeps it on a subpage, not the homepage."""
    base_row = None
    for url in job['urls']:
        result = prober.fetch(url)
        vendor, access = classify(result)
        row = {'probed_at': datetime.now(timezone.utc).isoformat(),
               'state': job['state'], 'county': job['county'], 'jail': job['jail'],
               'candidate_url': url, 'http_status': result.get('status'),
               'final_url': result.get('url'), 'vendor_family': vendor,
               'access_class': access, 'error': result.get('error') or '',
               'evidence': '', 'notes': ''}
        if access in ('vendor_portal', 'json_api', 'html_roster', 'pdf_roster', 'search_form'):
            row['evidence'] = url
            return row
        if access in ('captcha_gated', 'login_required'):
            base_row = base_row or row
            continue
        if access == 'no_roster_found' and follow and result.get('status') == 200:
            # Follow the site's own roster links first (they may be on another
            # domain); only fall back to guessing common paths.
            found = follow_links(prober, job, result.get('url') or url, result.get('body', ''))
            if not found:
                found = follow_roster(prober, job, origin_of(result['url'] or url))
            if found:
                return found
        base_row = base_row or row
    return base_row or {'probed_at': datetime.now(timezone.utc).isoformat(),
                        'state': job['state'], 'county': job['county'], 'jail': job['jail'],
                        'candidate_url': job['urls'][0] if job['urls'] else '',
                        'http_status': None, 'final_url': '', 'vendor_family': '',
                        'access_class': 'no_candidate', 'error': '', 'evidence': '', 'notes': ''}


FOUND_CLASSES = ('html_roster', 'json_api', 'pdf_roster', 'search_form', 'vendor_portal')
GATED_CLASSES = ('captcha_gated', 'login_required')


def _result_row(job: dict, url: str, result: dict, vendor: str, access: str,
                note: str) -> dict:
    return {'probed_at': datetime.now(timezone.utc).isoformat(),
            'state': job['state'], 'county': job['county'], 'jail': job['jail'],
            'candidate_url': url, 'http_status': result.get('status'),
            'final_url': result.get('url'), 'vendor_family': vendor,
            'access_class': access, 'error': result.get('error') or '',
            'evidence': url, 'notes': note}


def follow_links(prober: Prober, job: dict, base_url: str, body: str) -> dict | None:
    """Follow the page's own roster-ish links, including cross-domain ones.

    This is what actually finds rosters: measured on a 12-site sample, `/sheriff`
    guessed paths 404'd on 8, while 4 sites linked a real sheriff page — 2 of them
    on a different domain (`calcoso.org`, `blountalsheriff.org`).
    """
    for link in roster_links(body, base_url)[:LINKS_TO_TRY]:
        result = prober.fetch(link)
        vendor, access = classify(result)
        if access in FOUND_CLASSES:
            return _result_row(job, link, result, vendor, access, 'found via site link')
        if access in GATED_CLASSES:
            return _result_row(job, link, result, vendor, access, 'gated via site link')
    return None


def follow_roster(prober: Prober, job: dict, origin: str) -> dict | None:
    for path in ROSTER_PATHS[:ROSTER_PROBES]:
        url = origin + path
        result = prober.fetch(url)
        vendor, access = classify(result)
        if access in FOUND_CLASSES:
            return _result_row(job, url, result, vendor, access, 'found via common roster path')
        if access in GATED_CLASSES:
            return _result_row(job, url, result, vendor, access, 'gated on roster path')
    return None


def run_probes(jobs: list[dict], prober: Prober, out: Path, follow: bool,
               concurrency: int = 1) -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Resume: skip jobs already present in the output file so an interrupted run
    # continues instead of restarting.
    done = set()
    if out.exists() and out.stat().st_size:
        with out.open(newline='') as handle:
            for row in csv.DictReader(handle):
                if row.get('state') and row.get('county'):
                    done.add((row['state'], row['county'], row.get('jail', '')))
    pending = [j for j in jobs if (j['state'], j['county'], j.get('jail', '')) not in done]

    write_header = not out.exists() or out.stat().st_size == 0
    lock = threading.Lock()
    counter = {'n': 0, 'total': len(pending)}
    handle = out.open('a', newline='')
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if write_header:
        writer.writeheader()
        handle.flush()

    if done:
        print(f'  resuming: {len(done)} already classified, {len(pending)} to go')

    def work(job):
        return probe_one(prober, job, follow)

    try:
        if concurrency <= 1:
            for job in pending:
                row = work(job)
                with lock:
                    writer.writerow(row)
                    handle.flush()
                    counter['n'] += 1
                    print(f"  {row['state']:<3}{row['county'][:26]:<28}"
                          f"{row['access_class']:<18}"
                          f"{'(' + row['vendor_family'] + ')' if row['vendor_family'] else ''}")
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(work, job): job for job in pending}
                for future in as_completed(futures):
                    job = futures[future]
                    try:
                        row = future.result()
                    except Exception as error:  # never lose a whole run to one site
                        row = {'probed_at': datetime.now(timezone.utc).isoformat(),
                               'state': job['state'], 'county': job['county'],
                               'jail': job.get('jail', ''), 'candidate_url': '',
                               'http_status': None, 'final_url': '', 'vendor_family': '',
                               'access_class': 'probe_error',
                               'error': f'{type(error).__name__}', 'evidence': '', 'notes': ''}
                    with lock:
                        writer.writerow(row)
                        handle.flush()
                        counter['n'] += 1
                        if counter['n'] % 25 == 0 or counter['n'] == counter['total']:
                            print(f"  ... {counter['n']}/{counter['total']} classified")
    finally:
        handle.close()
    print(f'  finished {counter["n"]} probes '
          f'({concurrency} worker{"s" if concurrency != 1 else ""})')


def build_jobs_from_db(targets: list[dict], per_jail: int) -> list[dict]:
    return [{'state': t['state'], 'county': t['county'], 'jail': t['jail'],
             'urls': candidates(t['county'], t['state'])[:per_jail]} for t in targets]


def report(path: Path, by_state: bool) -> None:
    if not path.exists():
        print(f'no census at {path}', file=sys.stderr)
        return
    with path.open() as handle:
        rows = [r for r in csv.DictReader(handle) if r['access_class']]
    if not rows:
        print('census is empty')
        return
    access = Counter(r['access_class'] for r in rows)
    vendors = Counter(r['vendor_family'] for r in rows if r['vendor_family'])
    print(f'Source census — {len(rows)} jails classified\n')
    print('Access class')
    for name, count in access.most_common():
        print(f'  {name:<20} {count:>5}  {100.0*count/len(rows):>5.1f}%')
    print('\nVendor family (the leverage ranking)')
    if not vendors:
        print('  none detected yet')
    for name, count in vendors.most_common():
        print(f'  {name:<20} {count:>5}')
    if by_state:
        print('\nBy state')
        per: dict[str, Counter] = defaultdict(Counter)
        for row in rows:
            per[row['state']][row['access_class']] += 1
        for state in sorted(per, key=lambda s: -sum(per[s].values())):
            total = sum(per[state].values())
            live = total - per[state]['unreachable'] - per[state]['blocked']
            print(f'  {state:<4} {total:>4} jails  {live:>4} reachable  ' +
                  ', '.join(f'{k}={v}' for k, v in per[state].most_common(4)))


def main() -> int:
    parser = argparse.ArgumentParser(description='JailMap national source census')
    parser.add_argument('--sample', type=int, default=200, help='how many jails to probe')
    parser.add_argument('--states', type=int, default=10, help='span this many states (round-robin)')
    parser.add_argument('--per-jail', type=int, default=3, help='candidate URLs to try per jail')
    parser.add_argument('--active-only', action='store_true',
                        help='probe only the 7 hand-curated jails (rarely what you want)')
    parser.add_argument('--input', help='CSV of candidates (state,county,jail,url) instead of guessing')
    parser.add_argument('--no-follow', action='store_true', help='homepage only: no link following, no roster paths')
    parser.add_argument('--concurrency', type=int, default=1,
                        help='parallel workers ACROSS hosts (per-host 1 req/sec is always enforced)')
    parser.add_argument('--out', default='/src/data/national/source-census.csv')
    parser.add_argument('--dry-run', action='store_true', help='print candidates, no network')
    parser.add_argument('--no-robots', action='store_true', help='ignore robots.txt (do not use)')
    parser.add_argument('--report', help='print a report for an existing census CSV')
    parser.add_argument('--by-state', action='store_true', help='include per-state breakdown')
    args = parser.parse_args()

    if args.report:
        report(Path(args.report), args.by_state)
        return 0

    if args.input:
        jobs = read_input(Path(args.input))
        if not jobs:
            print(f'no usable rows in {args.input} (need a url column)', file=sys.stderr)
            return 1
    else:
        targets = load_targets(args.sample, args.states, args.active_only)
        if not targets:
            print('no targets returned', file=sys.stderr)
            return 1
        jobs = build_jobs_from_db(targets, args.per_jail)

    if args.dry_run:
        print(f'{len(jobs)} jails, up to {args.per_jail} candidate URLs each '
              f'(no network traffic)\n')
        for job in jobs[:25]:
            print(f"  {job['state']}  {job['county']}")
            for url in job['urls'][:args.per_jail]:
                print(f"      {url}")
        if len(jobs) > 25:
            print(f'  ... and {len(jobs) - 25} more')
        return 0

    out = Path(args.out)
    print(f'Probing {len(jobs)} jails -> {out}')
    print(f'robots={"obeyed" if not args.no_robots else "IGNORED"}  '
          f'{HOST_DELAY}s/host  timeout={TIMEOUT}s  max={MAX_BYTES}B  '
          f'roster-path-follow={"off" if args.no_follow else "on"}  '
          f'workers={max(1, args.concurrency)}\n')
    run_probes(jobs, Prober(respect_robots=not args.no_robots), out, not args.no_follow,
               concurrency=max(1, args.concurrency))
    print()
    report(out, args.by_state)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
