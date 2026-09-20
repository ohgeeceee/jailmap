from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.adapters import fl_smartweb

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class FloridaSmartWebTests(unittest.TestCase):
    def setUp(self):
        self.html = (FIXTURES / "fl_smartweb_jail.aspx").read_bytes()

    def test_extracts_inmates_from_putnam(self):
        class FakeResponse:
            status_code = 200
            text = self.html.decode("utf-8", errors="ignore")
            def raise_for_status(self): pass
        class FakeClient:
            def __init__(self, **kw): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def get(self, url, headers=None): return FakeResponse()

        with patch.object(fl_smartweb.httpx, "Client", FakeClient), \
             patch.object(fl_smartweb, "_assert_authorized", lambda url: None):
            source = {
                "county": "Putnam",
                "facility_name": "Putnam County Jail",
                "source_url": "https://smartweb.putnamsheriff.org/smartwebclient/jail.aspx",
            }
            result = fl_smartweb.fetch(source)
            self.assertGreaterEqual(len(result.records), 3)
            r0 = result.records[0]
            self.assertEqual(r0["booking_number"][:4], "PCSO")
            self.assertEqual(r0["status"], "in_custody")
            self.assertIsNotNone(r0["booking_date"])
            self.assertIsNotNone(r0["source_updated_at"])
            # Mugshot URL must not be published (expiring URLs)
            self.assertIsNone(r0["mugshot_url"])

    def test_standardizes_name(self):
        first, last = fl_smartweb._name_parts("BISHOP, AMY LEIGH")
        self.assertEqual(first, "Amy Leigh")
        self.assertEqual(last, "Bishop")

    def test_parses_date(self):
        parsed = fl_smartweb._parse_date("09/16/2026 07:05 AM")
        self.assertEqual(parsed, "2026-09-16T07:05:00-04:00")

    def test_status_mapping(self):
        self.assertEqual(fl_smartweb._status("In Jail"), "in_custody")
        self.assertEqual(fl_smartweb._status("Released"), "released")
        self.assertIsNone(fl_smartweb._status("Unknown"))

    def test_tls_verification_is_not_disabled(self):
        observed = {}

        class FakeResponse:
            text = self.html.decode("utf-8", errors="ignore")
            def raise_for_status(self): pass

        class FakeClient:
            def __init__(self, **kwargs): observed.update(kwargs)
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def get(self, url, headers=None): return FakeResponse()

        with patch.object(fl_smartweb.httpx, "Client", FakeClient), \
             patch.object(fl_smartweb, "_assert_authorized", lambda url: None):
            fl_smartweb.fetch({
                "state": "FL", "county": "Putnam", "facility_name": "Putnam County Jail",
                "source_url": "https://smartweb.example.gov/smartwebclient/jail.aspx",
            })
        self.assertNotIn("verify", observed)


if __name__ == "__main__":
    unittest.main()
