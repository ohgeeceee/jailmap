#!/usr/bin/env python3
"""Tests for the two-hop sheriff crawler.

Offline — network is mocked. The crawl logic is the product: link scoring,
two-hop ordering, and the handoff to the production classifier.
"""
import csv
import sys
import tempfile
import threading
import unittest
from pathlib import Path

# Ensure the script is importable.
# In the container, crawl_sheriff_links.py is mounted at /tools/.
sys.path.insert(0, '/tools')
# Fallback when running from the repo root: /root/jailmap/scripts/national
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts' / 'national'))

import crawl_sheriff_links as crawl


# --- fixtures ----------------------------------------------------------------
def county_page(sheriff_url: str) -> str:
    return f"""<html><body>
        <h1>County Homepage</h1>
        <a href="{sheriff_url}">Sheriff's Office</a>
        <a href="/contact">Contact Us</a>
    </body></html>"""


def sheriff_page(roster_url: str) -> str:
    return f"""<html><body>
        <h1>Sheriff's Office</h1>
        <a href="{roster_url}">Inmate Roster</a>
        <a href="/contact-sheriff">Contact</a>
    </body></html>"""


def roster_page() -> str:
    return """<html><body>
        <table>
            <tr><th>Name</th><th>Booking Date</th></tr>
            <tr><td>DOE, JOHN</td><td>2026-09-01</td></tr>
        </table>
    </body></html>"""


def search_page() -> str:
    return """<html><body>
        <form><input name="name" type="text"></form>
        <input type="submit" value="Search Inmate">
    </body></html>"""


def make_result(status, url, body, error=None, content_type='text/html'):
    return {'status': status, 'url': url, 'body': body, 'error': error,
            'content_type': content_type}


class CollectingWriter:
    """A DictWriter-like that collects rows instead of writing to a file."""

    def __init__(self, fields):
        self.fields = fields
        self.rows = []

    def writeheader(self):
        pass

    def writerow(self, row):
        self.rows.append(dict(row))


# --- tests -------------------------------------------------------------------
class TestFindLinks(unittest.TestCase):
    def test_finds_sheriff_link(self):
        body = '<a href="https://sheriff.example.gov/">Sheriff Department</a>'
        links = crawl.find_links(body, 'https://county.example.gov/',
                                 crawl.SHERIFF_HINTS)
        self.assertEqual(links, ['https://sheriff.example.gov/'])

    def test_prefers_same_origin(self):
        body = ('<a href="https://sheriff.example.gov/">Other Sheriff</a>'
                '<a href="/sheriff">Local Sheriff</a>')
        links = crawl.find_links(body, 'https://county.example.gov/',
                                 crawl.SHERIFF_HINTS)
        self.assertTrue(links[0].startswith('https://county.example.gov/'))

    def test_skips_mailto(self):
        body = '<a href="mailto:sheriff@example.gov">Email Sheriff</a>'
        links = crawl.find_links(body, 'https://county.example.gov/',
                                 crawl.SHERIFF_HINTS)
        self.assertEqual(links, [])

    def test_skips_pdf(self):
        body = '<a href="/sheriff/roster.pdf">Sheriff Roster PDF</a>'
        links = crawl.find_links(body, 'https://county.example.gov/',
                                 crawl.ROSTER_HINTS)
        self.assertEqual(links, [])

    def test_dedupes(self):
        body = ('<a href="/sheriff">Sheriff</a>'
                '<a href="/sheriff/">Sheriff</a>'
                '<a href="/sheriff">Sheriff</a>')
        links = crawl.find_links(body, 'https://county.example.gov/',
                                 crawl.SHERIFF_HINTS)
        self.assertEqual(len(links), 1)

    def test_roster_link_scoring(self):
        """Roster link with 'inmate' in anchor text scores higher."""
        body = ('<a href="/sheriff">Sheriff Home</a>'
                '<a href="/inmate-search">Search Inmates</a>')
        links = crawl.find_links(body, 'https://county.example.gov/',
                                 crawl.ROSTER_HINTS)
        # Both match; the one mentioning "inmate" should be first.
        self.assertIn('inmate-search', links[0])


class TestBuildLead(unittest.TestCase):
    def test_html_roster_lead(self):
        lead = crawl._build_lead(
            'MT', 'Cascade', 'Cascade County Jail',
            'https://sheriff.mt.gov/roster', 'https://cascade.mt.gov/',
            'https://sheriff.mt.gov', '', 'html_roster')
        self.assertEqual(lead['state'], 'MT')
        self.assertEqual(lead['source_url'], 'https://sheriff.mt.gov/roster')
        self.assertEqual(lead['source_kind'], 'html_roster')
        self.assertEqual(lead['adapter_strategy'], 'html_roster')
        self.assertEqual(lead['publication_default'], 'staging_only')
        self.assertEqual(lead['access_status'], 'needs_adapter')
        # Two-hop evidence recorded in notes.
        self.assertIn('https://cascade.mt.gov/', lead['notes'])
        self.assertIn('https://sheriff.mt.gov/roster', lead['notes'])

    def test_gated_lead(self):
        lead = crawl._build_lead(
            'MT', 'Cascade', 'Cascade County Jail',
            'https://sheriff.mt.gov/roster', 'https://cascade.mt.gov/',
            'https://sheriff.mt.gov', '', 'captcha_gated')
        self.assertEqual(lead['access_status'], 'blocked')
        self.assertEqual(lead['publication_default'], 'staging_only')

    def test_vendor_lead(self):
        lead = crawl._build_lead(
            'MT', 'Cascade', 'Cascade County Jail',
            'https://sheriff.mt.gov/roster', 'https://cascade.mt.gov/',
            'https://sheriff.mt.gov', 'zuercher', 'vendor_portal')
        self.assertEqual(lead['source_kind'], 'zuercher_portal')
        self.assertEqual(lead['adapter_strategy'], 'zuercher_portal')
        self.assertEqual(lead['access_status'], 'needs_adapter')

    def test_search_form_lead(self):
        lead = crawl._build_lead(
            'MT', 'Cascade', 'Cascade County Jail',
            'https://sheriff.mt.gov/lookup', 'https://cascade.mt.gov/',
            'https://sheriff.mt.gov', '', 'search_form')
        self.assertEqual(lead['source_kind'], 'search_form')
        self.assertEqual(lead['adapter_strategy'], 'search_form')


class TestCrawlOne(unittest.TestCase):
    def setUp(self):
        self.prober = crawl.Prober()
        self.prober._throttle = lambda host: None
        self.prober.robots = {}  # skip robots fetching
        self.done = set()
        self.lock = threading.Lock()
        self.counter = {'found': 0, 'gated': 0, 'no_roster': 0, 'unreachable': 0}
        self.writer = CollectingWriter(crawl.FIELDS)

    def test_two_hop_html_roster(self):
        """Homepage -> sheriff -> roster table found."""
        def mock_fetch(url):
            if url == 'https://cascade.mt.gov/':
                return make_result(200, url, county_page('https://sheriff.mt.gov/'))
            if url == 'https://sheriff.mt.gov/':
                return make_result(200, url, sheriff_page('https://sheriff.mt.gov/roster'))
            if url == 'https://sheriff.mt.gov/roster':
                return make_result(200, url, roster_page())
            return make_result(404, url, '')

        self.prober.fetch = mock_fetch

        candidate = {
            'state': 'MT', 'county': 'Cascade', 'jail': 'Cascade County Jail',
            'url': 'https://cascade.mt.gov/'
        }
        crawl.crawl_one(self.prober, candidate, self.writer, self.done,
                        self.lock, self.counter)

        self.assertEqual(self.counter['found'], 1)
        self.assertEqual(len(self.writer.rows), 1)
        self.assertEqual(self.writer.rows[0]['source_kind'], 'html_roster')

    def test_homepage_is_roster(self):
        """Homepage itself is a roster -- no need to crawl further."""
        def mock_fetch(url):
            if url == 'https://county.mt.gov/':
                return make_result(200, url, roster_page())
            return make_result(404, url, '')

        self.prober.fetch = mock_fetch

        candidate = {
            'state': 'MT', 'county': 'Test', 'jail': 'Test Jail',
            'url': 'https://county.mt.gov/'
        }
        crawl.crawl_one(self.prober, candidate, self.writer, self.done,
                        self.lock, self.counter)

        self.assertEqual(self.counter['found'], 1)
        self.assertEqual(self.writer.rows[0]['source_kind'], 'html_roster')

    def test_unreachable_homepage(self):
        def mock_fetch(url):
            return make_result(None, url, '', error='ConnectError')

        self.prober.fetch = mock_fetch

        candidate = {
            'state': 'MT', 'county': 'Test', 'jail': 'Test Jail',
            'url': 'https://county.mt.gov/'
        }
        crawl.crawl_one(self.prober, candidate, self.writer, self.done,
                        self.lock, self.counter)

        self.assertEqual(self.counter['unreachable'], 1)
        self.assertEqual(len(self.writer.rows), 0)

    def test_search_form_found(self):
        def mock_fetch(url):
            if url == 'https://county.mt.gov/':
                return make_result(200, url, county_page('https://sheriff.mt.gov/'))
            if url == 'https://sheriff.mt.gov/':
                return make_result(200, url, sheriff_page('https://sheriff.mt.gov/lookup'))
            if url == 'https://sheriff.mt.gov/lookup':
                return make_result(200, url, search_page())
            return make_result(404, url, '')

        self.prober.fetch = mock_fetch

        candidate = {
            'state': 'MT', 'county': 'Test', 'jail': 'Test Jail',
            'url': 'https://county.mt.gov/'
        }
        crawl.crawl_one(self.prober, candidate, self.writer, self.done,
                        self.lock, self.counter)

        self.assertEqual(self.counter['found'], 1)
        self.assertEqual(self.writer.rows[0]['source_kind'], 'search_form')

    def test_no_roster_anywhere(self):
        def mock_fetch(url):
            if url == 'https://county.mt.gov/':
                return make_result(200, url, '<html><body><p>No sheriff link</p></body></html>')
            return make_result(404, url, '')

        self.prober.fetch = mock_fetch

        candidate = {
            'state': 'MT', 'county': 'Test', 'jail': 'Test Jail',
            'url': 'https://county.mt.gov/'
        }
        crawl.crawl_one(self.prober, candidate, self.writer, self.done,
                        self.lock, self.counter)

        self.assertEqual(self.counter['no_roster'], 1)
        self.assertEqual(len(self.writer.rows), 0)

    def test_sheriff_gated_at_hop2(self):
        """Sheriff page itself is captcha-gated."""
        def mock_fetch(url):
            if url == 'https://county.mt.gov/':
                return make_result(200, url, county_page('https://sheriff.mt.gov/'))
            if url == 'https://sheriff.mt.gov/':
                return make_result(200, url, '<html><body class="cf-chl-">captcha</body></html>')
            return make_result(404, url, '')

        self.prober.fetch = mock_fetch

        candidate = {
            'state': 'MT', 'county': 'Test', 'jail': 'Test Jail',
            'url': 'https://county.mt.gov/'
        }
        crawl.crawl_one(self.prober, candidate, self.writer, self.done,
                        self.lock, self.counter)

        self.assertEqual(self.counter['gated'], 1)
        self.assertEqual(len(self.writer.rows), 1)
        self.assertEqual(self.writer.rows[0]['access_status'], 'blocked')


class TestReadCandidates(unittest.TestCase):
    def test_reads_csv(self):
        handle = tempfile.NamedTemporaryFile('w', newline='', delete=False)
        with handle:
            writer = csv.DictWriter(handle,
                                    fieldnames=['state', 'county', 'jail', 'url'])
            writer.writeheader()
            writer.writerow({
                'state': 'MT', 'county': 'Cascade',
                'jail': 'Cascade County Jail',
                'url': 'https://cascade.mt.gov/'})
        path = Path(handle.name)
        try:
            candidates = crawl.read_candidates(path)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]['state'], 'MT')
            self.assertEqual(candidates[0]['url'], 'https://cascade.mt.gov/')
        finally:
            path.unlink()


if __name__ == '__main__':
    unittest.main()
