from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.adapters import maricopa_html


class MaricopaAdapterTests(unittest.TestCase):
    def test_maricopa_parser_counts_and_fields(self):
        maricopa_html._fetch_html = lambda url: Path(
            "/root/jailmap/backend/tests/fixtures/maricopa_raw.html"
        ).read_bytes()
        source = {
            "county": "Maricopa",
            "state": "AZ",
            "facility_name": "Maricopa County Jail",
            "source_url": "https://portal.mobileso.com/mcso/jail/jp_ci_c.asp",
            "source_type": "custom_html",
            "adapter_strategy": "html_table",
        }
        result = maricopa_html.parse(source)
        # Should have parsed many records from the full fixture
        self.assertGreater(len(result.records), 100)
        # Check first record
        first = result.records[0]
        self.assertEqual(first["booking_number"], "202600010167")
        self.assertEqual(first["first_name"], "RYAN")
        self.assertEqual(first["last_name"], "ABNER")
        self.assertEqual(first["sex"], "MALE")
        self.assertEqual(first["race"], "BLACK")
        self.assertEqual(first["age"], 31)
        self.assertEqual(first["status"], "in_custody")
        self.assertEqual(first["state"], "AZ")
        self.assertEqual(first["county"], "Maricopa")

    def test_maricopa_parser_handles_alternating_row_classes(self):
        maricopa_html._fetch_html = lambda url: Path(
            "/root/jailmap/backend/tests/fixtures/maricopa_raw.html"
        ).read_bytes()
        source = {
            "county": "Maricopa",
            "state": "AZ",
            "facility_name": "Maricopa County Jail",
            "source_url": "https://portal.mobileso.com/mcso/jail/jp_ci_c.asp",
            "source_type": "custom_html",
            "adapter_strategy": "html_table",
        }
        result = maricopa_html.parse(source)
        # Should have both ctd and cdt rows
        self.assertGreater(len(result.records), 50)
        # Check that we have records with different booking number formats
        booking_numbers = [r["booking_number"] for r in result.records]
        self.assertTrue(all(len(bn) == 12 for bn in booking_numbers))


if __name__ == "__main__":
    unittest.main()
