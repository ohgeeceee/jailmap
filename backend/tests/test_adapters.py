from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.adapters import bonneville_html, power_html, franklin_html, owyhee_pdf

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class IdahoAdapterTests(unittest.TestCase):
    def test_bonneville_parser_counts_and_fields(self):
        bonneville_html._fetch_html = lambda url: (FIXTURES / "bonneville_inmate_list.html").read_bytes()
        source = {
            "county": "Bonneville",
            "state": "ID",
            "facility_name": "Bonneville County Jail",
            "source_url": "http://bonnevillesheriff.com/bonneville-county-jail/inmate-list/",
            "source_type": "custom_html",
            "adapter_strategy": "html_table",
        }
        result = bonneville_html.parse(source)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.records[0]["inmate_id"], "719")
        self.assertTrue(result.records[0]["mugshot_url"].endswith(".jpg"))
        self.assertEqual(result.records[0]["full_name"], "TYSON COOK")

    def test_power_parser_lists_inmate_links(self):
        power_html._fetch_html = lambda url: (FIXTURES / "power_roster_list.html").read_bytes()
        source = {
            "county": "Power",
            "state": "ID",
            "facility_name": "Power County Jail",
            "source_url": "https://jail.powercounty.gov/jailroster/",
            "source_type": "custom_html",
            "adapter_strategy": "link_list",
        }
        result = power_html.parse(source)
        self.assertEqual(len(result.records), 2)
        self.assertIsNone(result.records[0]["booking_number"])
        self.assertEqual(result.records[0]["full_name"], "MARLON BARRIENTOS MORAN")

    def test_franklin_parser_extracts_booking_and_bond(self):
        franklin_html._fetch_html = lambda url: (FIXTURES / "franklin_roster_block.html").read_bytes()
        source = {
            "county": "Franklin",
            "state": "ID",
            "facility_name": "Franklin County Jail",
            "source_url": "https://www.franklinsheriff.org/roster.php",
            "source_type": "custom_html",
            "adapter_strategy": "booking_block",
        }
        result = franklin_html.parse(source)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record["booking_number"], "6690")
        self.assertEqual(record["bond_amount"], 0.0)
        self.assertTrue(record["mugshot_url"].endswith(".jpg"))
        self.assertEqual(record["full_name"], "WILLIAM MURRAY")

    def test_owyhee_pdf_fallback_returns_empty_when_no_pdf_text(self):
        owyhee_pdf._fetch_html = lambda url: (FIXTURES / "owyhee_jail_page.html").read_bytes()

        def fake_pdf_text(url):
            return None

        source = {
            "county": "Owyhee",
            "state": "ID",
            "facility_name": "Owyhee County Jail",
            "source_url": "https://owyheecounty.net/sheriff/jail/",
            "source_type": "pdf",
            "adapter_strategy": "linked_pdf",
        }
        result = owyhee_pdf.parse(source, pdf_text_provider=fake_pdf_text)
        self.assertEqual(result.records, [])


if __name__ == "__main__":
    unittest.main()
