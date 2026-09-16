#!/usr/bin/env python3
"""Two-hop sheriff-link crawler for JailMap source discovery.

The national census proved that guessing roster paths fails: on commission sites
`/sheriff` returns 404 on 8 of 12, while the real link is
`/departments/sheriffs-department`, `/31/Sheriffs-Department`, or a different
domain entirely (`calcoso.org`, `blountalsheriff.org`). A probe that only guesses
paths reaches ~4% of the remainder. This crawler follows the site's own links.

Two hops:
  Hop 1: county homepage  →  find links to a sheriff site
  Hop 2: sheriff page      →  find the roster page and classify it

Output is a source-lead CSV matching import_source_leads.py format:
  state, county, facility, source_url, source_owner, source_kind,
  access_status, adapter_strategy, publication_default, evidence_url, notes

Green-tier only: writes a CSV, touches nothing else.

Design constraints (MISSION.md):
  * robots.txt fetched and obeyed for every host before any page fetch.
  * One request per host per second, sequential, bounded concurrency.
  * No captcha solving, no login attempt, no paywall circumvention.
  * Bounded response size and timeout; a slow site is skipped, not hammered.
  * --dry-run prints the candidate URLs and exits WITHOUT any network traffic.
  * Per-source results are written incrementally so an interrupted run can
    resume.

Run via scripts/national/run.sh crawl_sheriff_links.py ...
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import threading
import time
import urllib.robotparser
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

REPO = Path(os.environ.get('JAILMAP_REPO') or '/src')

USER_AGENT = 'JailMapBot/1.0 (+https://jailmap.com/sources; source discovery)'
TIMEOUT = 12.0
MAX_BYTES = 400_000
HOST_DELAY = 1.0

# --- link hints --------------------------------------------------------------
# Hop 1: anything on a county site that looks like a sheriff link.
SHERIFF_HINTS = ('sheriff', "sheriff's office", 'sheriffs office')
# Hop 2: anything on a sheriff site that looks like a roster link.
ROSTER_HINTS = ('inmate', 'roster', 'booking', 'custody', 'detainee',
                'current inmates', "who's in jail", 'jail population',
                'inmate search', 'inmate lookup', 'lookup', 'search')
LINKS_TO_TRY = 4
SKIP_EXT = ('.pdf', '.jpg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls',
            '.mp4', '.mov', '.avi')

# --- vendor fingerprint table ------------------------------------------------
VENDORS = [
    ('zuercher',          ('zuercherportal.com',), ('zuercher',)),
    ('socrata_open_data', ('socrata', 'sharefulton', 'opendata'), ('socrata',)),
    ('tyler_jailtracker', ('jailtracker',), ('jailtracker',)),
    ('tyler_odyssey',     ('odyssey', 'tylertech'), ('tyler technologies',)),
    ('smartweb',          ('smartweb', 'netvision', 'inmatelookup',
                           'inmate-lookup'), ('netvision',)),
    ('citizenrims',       ('citizenrims',), ('citizenrims',)),
]

CAPTCHA_MARKERS = ('g-recaptcha', 'hcaptcha', 'cf-chl-', 'turnstile',
                   'are you a human', 'verify you are human')
LOGIN_MARKERS = ('type="password"', "type='password'", 'name="password"',
                 'sign in to continue')
ROSTER_KEYWORDS = ('inmate', 'roster', 'booking', 'custody', 'detainee')


# --- HTTP client --------------------------------------------------------------
class Prober:
    """Robots-aware, per-host rate-limited fetcher. Never passes a gate."""

    def __init__(self):
        import httpx
        self.client = httpx.Client(timeout=TIMEOUT, follow_redirects=True,
                                   headers={'user-agent': USER_AGENT,
                                            'accept': 'text/html,application/xhtml+xml,application/json,application/pdf'})
        self.robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.last_hit: dict[str, float] = {}
        self._lock = threading.Lock()

    def allowed(self, url: str) -> bool:
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
                    parser = None
            except Exception:
                parser = None
            with self._lock:
                self.robots[origin] = parser
        with self._lock:
            parser = self.robots[origin]
        return True if parser is None else parser.can_fetch(USER_AGENT, url)

    def _throttle(self, host: str) -> None:
        with self._lock:
            now = time.time()
            nxt = max(now, self.last_hit.get(host, 0.0) + HOST_DELAY)
            self.last_hit[host] = nxt
        delay = nxt - time.time()
        if delay > 0:
            time.sleep(delay)

    def fetch(self, url: str) -> dict:
        if not self.allowed(url):
            return {'status': None, 'error': 'robots_disallowed', 'url': url,
                    'body': '', 'content_type': ''}
        self._throttle(urlsplit(url).netloc)
        try:
            with self.client.stream('GET', url) as response:
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        break
                return {'status': response.status_code, 'url': str(response.url),
                        'error': None,
                        'body': bytes(body).decode('utf-8', 'ignore'),
                        'content_type': response.headers.get('content-type', '')}
        except Exception as error:
            return {'status': None, 'error': type(error).__name__, 'url': url,
                    'body': '', 'content_type': ''}


# --- link extraction ---------------------------------------------------------
def _extract_anchors(body: str) -> list[tuple[str, str]]:
    """Return (href, text) for every anchor in the body."""
    return re.findall(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                      body, re.I | re.S)


def _score_and_order(links: list[tuple[int, int, str]]) -> list[str]:
    """Dedupe and order scored links (highest score first)."""
    links.sort()
    seen, ordered = set(), []
    for _, _, url in links:
        key = url.rstrip('/')
        if key not in seen:
            seen.add(key)
            ordered.append(url)
    return ordered


def find_links(body: str, base_url: str, hints: list[str],
               same_origin_first: bool = True) -> list[str]:
    """Find anchors matching any hint. Same-origin links first by default."""
    hrefs = _extract_anchors(body)
    base_host = urlsplit(base_url).netloc
    scored: list[tuple[int, int, str]] = []
    for href, text in hrefs:
        href = href.strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue
        blob = (href + ' ' + re.sub(r'<[^>]+>', ' ', text)).lower()
        if not any(hint in blob for hint in hints):
            continue
        absolute = urljoin(base_url, href)
        if not absolute.startswith('https://'):
            continue
        if absolute.lower().endswith(SKIP_EXT):
            continue
        score = sum(1 for hint in hints if hint in blob)
        same = 1 if urlsplit(absolute).netloc == base_host else 0
        scored.append((-score, -same if same_origin_first else same, absolute))
    return _score_and_order(scored)


# --- classification ----------------------------------------------------------
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
    for family, host_needles, _ in VENDORS:
        if any(n in final for n in host_needles):
            vendor = family
            break
    if not vendor:
        for family, _, body_needles in VENDORS:
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
    # Require real roster structure — the html_roster parser's column mapping.
    tables, _rows = _roster_tables(body)
    if tables:
        return vendor, 'html_roster'
    if '<form' in body and any(k in body for k in ROSTER_KEYWORDS):
        return vendor, 'search_form'
    return vendor, 'no_roster_found'


def _roster_tables(body: str) -> tuple[int, int]:
    """Tables carrying a person-identity column, estimated data rows."""
    # Local import so the script runs without the backend on the path.
    try:
        sys.path.insert(0, str(REPO))
        from backend.adapters.html_roster import (IDENTITY_FIELDS,
                                                  _TableExtractor, _map_columns)
    except Exception:
        return 0, 0
    if not body:
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


# --- the crawl itself --------------------------------------------------------
FOUND_CLASSES = ('html_roster', 'json_api', 'pdf_roster', 'search_form',
                 'vendor_portal')
GATED_CLASSES = ('captcha_gated', 'login_required')


def _owner_from_url(url: str) -> str:
    host = urlsplit(url).netloc
    host = re.sub(r'^www\.', '', host)
    return host


def _build_lead(state: str, county: str, facility: str, roster_url: str,
                hop1_url: str, hop2_url: str, vendor: str,
                access: str) -> dict:
    """Build one source-lead row in import_source_leads.py format."""
    owner = _owner_from_url(roster_url)
    if vendor:
        kind = f'{vendor}_portal'
        strategy = f'{vendor}_portal'
    elif access == 'html_roster':
        kind, strategy = 'html_roster', 'html_roster'
    elif access == 'search_form':
        kind, strategy = 'search_form', 'search_form'
    elif access == 'pdf_roster':
        kind, strategy = 'pdf_roster', 'pdf_roster'
    elif access == 'json_api':
        kind, strategy = 'json_api', 'json_api'
    elif access in GATED_CLASSES:
        kind = access
        strategy = 'manual_discovery'
    else:
        kind, strategy = access, 'manual_discovery'

    if access in GATED_CLASSES:
        status = 'blocked'
    elif access == 'no_roster_found':
        status = 'no_public_source'
    else:
        status = 'needs_adapter'

    notes = (f'Two-hop crawl: {hop1_url} -> {hop2_url} -> {roster_url}. '
             f'access={access}. {"vendor=" + vendor if vendor else ""} '
             f'Official roster source; publication_default=staging_only pending review.')

    return {
        'state': state,
        'county': county,
        'facility': facility,
        'source_url': roster_url,
        'source_owner': owner,
        'source_kind': kind,
        'access_status': status,
        'adapter_strategy': strategy,
        'publication_default': 'staging_only',
        'evidence_url': roster_url,
        'notes': notes[:3000],
    }


def crawl_one(prober: Prober, candidate: dict, writer, done: set,
              lock: threading.Lock, counter: dict,
              max_sheriff_links: int = 3) -> None:
    """Crawl one candidate: homepage -> sheriff -> roster."""
    homepage_url = candidate['url']
    state = candidate['state']
    county = candidate['county']
    facility = candidate.get('jail', '')
    key = (state, county, homepage_url)

    # Hop 1: fetch the homepage.
    result = prober.fetch(homepage_url)
    vendor, access = classify(result)

    # If the homepage itself is a roster (rare for no-roster candidates), done.
    if access in FOUND_CLASSES:
        lead = _build_lead(state, county, facility, result['url'],
                           homepage_url, homepage_url, vendor, access)
        with lock:
            writer.writerow(lead)
            done.add(key)
            counter['found'] += 1
        return
    if access in GATED_CLASSES:
        # Record the gated homepage so we know we tried.
        lead = _build_lead(state, county, facility, result['url'],
                           homepage_url, homepage_url, vendor, access)
        with lock:
            writer.writerow(lead)
            done.add(key)
            counter['gated'] += 1
        return
    if access == 'unreachable' or not result.get('body'):
        with lock:
            done.add(key)
            counter['unreachable'] += 1
        return

    # Hop 2: find sheriff links on the homepage.
    hop1_url = result.get('url') or homepage_url
    sheriff_links = find_links(result['body'], hop1_url,
                               SHERIFF_HINTS)[:max_sheriff_links]

    found = False
    for sheriff_url in sheriff_links:
        s_result = prober.fetch(sheriff_url)
        s_vendor, s_access = classify(s_result)

        if s_access in FOUND_CLASSES:
            lead = _build_lead(state, county, facility, s_result['url'],
                               hop1_url, sheriff_url, s_vendor, s_access)
            with lock:
                writer.writerow(lead)
                counter['found'] += 1
            found = True
            break
        if s_access in GATED_CLASSES:
            lead = _build_lead(state, county, facility, s_result['url'],
                               hop1_url, sheriff_url, s_vendor, s_access)
            with lock:
                writer.writerow(lead)
                counter['gated'] += 1
            found = True
            break
        if s_access == 'unreachable' or not s_result.get('body'):
            continue

        # Hop 2b: find roster links on the sheriff page.
        hop2_url = s_result.get('url') or sheriff_url
        roster_links = find_links(s_result['body'], hop2_url,
                                  ROSTER_HINTS)[:LINKS_TO_TRY]
        for roster_url in roster_links:
            r_result = prober.fetch(roster_url)
            r_vendor, r_access = classify(r_result)
            if r_access in FOUND_CLASSES:
                lead = _build_lead(state, county, facility, r_result['url'],
                                   hop1_url, hop2_url + ' -> ' + roster_url,
                                   r_vendor, r_access)
                with lock:
                    writer.writerow(lead)
                    counter['found'] += 1
                found = True
                break
            if r_access in GATED_CLASSES:
                lead = _build_lead(state, county, facility, r_result['url'],
                                   hop1_url, hop2_url + ' -> ' + roster_url,
                                   r_vendor, r_access)
                with lock:
                    writer.writerow(lead)
                    counter['gated'] += 1
                found = True
                break
        if found:
            break

    with lock:
        done.add(key)
        if not found:
            counter['no_roster'] += 1


def read_candidates(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8-sig') as handle:
        return [
            {
                'state': r['state'].strip(),
                'county': r['county'].strip(),
                'jail': (r.get('jail') or '').strip(),
                'url': r['url'].strip(),
            }
            for r in csv.DictReader(handle)
            if r.get('state') and r.get('county') and r.get('url')
        ]


FIELDS = [
    'state', 'county', 'facility', 'source_url', 'source_owner', 'source_kind',
    'access_status', 'adapter_strategy', 'publication_default', 'evidence_url',
    'notes',
]


def run_crawl(candidates: list[dict], out: Path, prober: Prober,
              max_sheriff_links: int = 3, concurrency: int = 1) -> dict:
    """Run the crawl and return counters."""
    done = set()
    if out.exists() and out.stat().st_size:
        with out.open(newline='', encoding='utf-8-sig') as handle:
            for row in csv.DictReader(handle):
                if row.get('state') and row.get('county') and row.get('source_url'):
                    # Recover the homepage URL from the notes column.
                    notes = row.get('notes', '')
                    match = re.search(r'^Two-hop crawl: (https?://\S+) ->', notes)
                    if match:
                        done.add((row['state'], row['county'], match.group(1)))

    pending = [c for c in candidates
               if (c['state'], c['county'], c['url']) not in done]

    write_header = not out.exists() or out.stat().st_size == 0
    lock = threading.Lock()
    counter = Counter({'found': 0, 'gated': 0, 'no_roster': 0, 'unreachable': 0})

    handle = out.open('a', newline='', encoding='utf-8-sig')
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if write_header:
        writer.writeheader()
        handle.flush()

    print(f'  {len(pending)} to crawl ({len(done)} already done)')

    def work(candidate):
        crawl_one(prober, candidate, writer, done, lock, counter,
                  max_sheriff_links=max_sheriff_links)

    try:
        if concurrency <= 1:
            for i, candidate in enumerate(pending, 1):
                work(candidate)
                if i % 10 == 0 or i == len(pending):
                    print(f'  ... {i}/{len(pending)} crawled  '
                          f'(found={counter["found"]} gated={counter["gated"]} '
                          f'none={counter["no_roster"]} dead={counter["unreachable"]})')
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(work, c): c for c in pending}
                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        future.result()
                    except Exception:
                        pass
                    if i % 10 == 0 or i == len(pending):
                        with lock:
                            print(f'  ... {i}/{len(pending)} crawled  '
                                  f'(found={counter["found"]} gated={counter["gated"]} '
                                  f'none={counter["no_roster"]} dead={counter["unreachable"]})')
    finally:
        handle.flush()
        handle.close()

    return dict(counter)


def main() -> int:
    parser = argparse.ArgumentParser(description='JailMap two-hop sheriff crawler')
    parser.add_argument('--input', type=Path,
                        default=REPO / 'data' / 'national' / 'candidates-noroster.csv',
                        help='CSV of candidates with no roster found at homepage depth')
    parser.add_argument('--out', type=Path,
                        default=REPO / 'data' / 'national' / 'sheriff-crawl-leads.csv',
                        help='Output source-lead CSV')
    parser.add_argument('--max-sheriff-links', type=int, default=3,
                        help='Max sheriff links to follow per county')
    parser.add_argument('--concurrency', type=int, default=1,
                        help='Parallel workers ACROSS hosts')
    parser.add_argument('--limit', type=int, default=0,
                        help='Stop after this many candidates')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print candidates, no network')
    args = parser.parse_args()

    candidates = read_candidates(args.input)
    if args.limit:
        candidates = candidates[:args.limit]

    if args.dry_run:
        print(f'{len(candidates)} candidates (no network traffic)\n')
        for c in candidates[:25]:
            print(f"  {c['state']}  {c['county']}  {c['url']}")
        if len(candidates) > 25:
            print(f'  ... and {len(candidates) - 25} more')
        return 0

    print(f'Two-hop crawl: {len(candidates)} candidates -> {args.out}')
    print(f'max_sheriff_links={args.max_sheriff_links}  '
          f'{HOST_DELAY}s/host  timeout={TIMEOUT}s  workers={args.concurrency}\n')

    prober = Prober()
    stats = run_crawl(candidates, args.out, prober,
                      max_sheriff_links=args.max_sheriff_links,
                      concurrency=args.concurrency)

    print(f'\nDone: found={stats["found"]} gated={stats["gated"]} '
          f'none={stats["no_roster"]} dead={stats["unreachable"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
