import json
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from backend.ingestion.adapters.html_table import HtmlTableAdapter
from backend.ingestion.adapters.json_api import JsonApiAdapter
from backend.ingestion.adapters.common import decimal_value
from backend.ingestion.adapters.minnehaha import MinnehahaRosterAdapter
from backend.ingestion.base import AdapterConfig
from backend.ingestion.models import BookingRecord, Charge
from backend.ingestion.worker import booking_upsert_sql
from backend.ingestion.cli import main


FACILITY_ID = "clx-test-facility"


class BookingRecordTests(unittest.TestCase):
    def test_non_monetary_no_bond_value_is_unknown(self):
        self.assertIsNone(decimal_value("No Bond"))
        self.assertIsNone(decimal_value("Sentenced"))

    def test_serializes_normalized_record(self):
        record = BookingRecord(
            facility_id=FACILITY_ID,
            booking_number="  A-10 ",
            first_name=" Jane ",
            last_name=" Doe ",
            booking_date=datetime(2026, 9, 20, tzinfo=timezone.utc),
            charges=(Charge(charge_description="Theft", bond_amount=Decimal("50.25")),),
            total_bond_amount=Decimal("50.25"),
        )
        payload = record.to_dict()
        self.assertEqual(payload["booking_number"], "A-10")
        self.assertEqual(payload["first_name"], "Jane")
        self.assertEqual(payload["charges"][0]["bond_amount"], "50.25")
        self.assertTrue(payload["scraped_at"].endswith("+00:00"))

    def test_rejects_naive_booking_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            BookingRecord(
                facility_id=FACILITY_ID,
                booking_number="A-11",
                first_name="Jane",
                last_name="Doe",
                booking_date=datetime(2026, 9, 20),
            )


class AdapterTests(unittest.TestCase):
    def test_minnehaha_explicit_column_mapping(self):
        html = """<table class='tablesorter'><tbody><tr>
          <td>Jane</td><td>Q</td><td>Doe</td><td>12345</td>
          <td>2026-09-20</td><td>10:30</td><td>Jail</td><td>No Bond</td><td>Theft</td>
        </tr><tr><td>Sam</td><td></td><td>Lee</td><td>99999</td>
          <td>09/20/2026</td><td>11:30 AM</td><td>EM</td><td>0</td><td></td></tr></tbody></table>"""
        client = Mock()
        response = Mock(text=html)
        response.raise_for_status.return_value = None
        client.get.return_value = response
        adapter = MinnehahaRosterAdapter(AdapterConfig(
            facility_id=FACILITY_ID, source_url="https://example.gov", timezone="America/Chicago"
        ), client=client)
        records = adapter.run()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].booking_number, "12345")
        self.assertEqual(records[0].last_name, "Doe")
        self.assertEqual(records[0].charges[0].charge_description, "Theft")

    def test_ingest_cli_requires_explicit_commit(self):
        with self.assertRaisesRegex(SystemExit, "without --commit"):
            main(["ingest", "--config", "unused.json"])

    def test_html_table_adapter(self):
        response = Mock()
        response.text = """
          <table id='roster'><tr><th>Booking #</th><th>Name</th><th>Booked</th><th>Charge</th></tr>
          <tr><td>42</td><td>Doe, Jane Q</td><td>2026-09-20T12:00:00+00:00</td><td>Theft</td></tr></table>
        """
        response.raise_for_status.return_value = None
        client = Mock()
        client.get.return_value = response
        adapter = HtmlTableAdapter(
            AdapterConfig(
                facility_id=FACILITY_ID,
                source_url="https://example.gov/roster",
                options={"table_selector": "#roster", "row_filters": {"charges": ["Theft"]}},
            ),
            client=client,
        )
        records = adapter.run()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].last_name, "Doe")
        self.assertEqual(records[0].charges[0].charge_description, "Theft")

    def test_json_adapter_stops_at_empty_page(self):
        responses = []
        for data in [
            {"results": [{"id": "99", "first": "Sam", "last": "Lee", "booked": "2026-09-20T10:00:00Z"}]},
            {"results": []},
        ]:
            response = Mock()
            response.json.return_value = data
            response.raise_for_status.return_value = None
            responses.append(response)
        client = Mock()
        client.get.side_effect = responses
        adapter = JsonApiAdapter(
            AdapterConfig(
                facility_id=FACILITY_ID,
                source_url="https://example.gov/api",
                options={"items_path": "results", "field_map": {"booking_number": "id", "first_name": "first", "last_name": "last", "booking_date": "booked"}},
            ),
            client=client,
        )
        records = adapter.run()
        self.assertEqual([r.booking_number for r in records], ["99"])
        self.assertEqual(client.get.call_count, 2)

    def test_upsert_does_not_reset_review_state(self):
        sql = booking_upsert_sql()
        self.assertIn("ON CONFLICT (facility_id, booking_number)", sql)
        self.assertNotIn("publication_state = EXCLUDED", sql)

    def test_cli_summary_only_does_not_export_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/config.json"
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"facility_id": FACILITY_ID, "source_url": "https://example.gov", "vendor": "html_table"}, handle)
            with unittest.mock.patch("backend.ingestion.cli.build_adapter") as build:
                build.return_value.config.facility_id = FACILITY_ID
                build.return_value.run.return_value = [Mock(), Mock()]
                self.assertEqual(main(["run", "--config", path, "--summary-only"]), 0)
                build.return_value.export.assert_not_called()


if __name__ == "__main__":
    unittest.main()
