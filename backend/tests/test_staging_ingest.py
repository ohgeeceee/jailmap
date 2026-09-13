from datetime import datetime, timezone
import unittest

from backend.staging import prepare_staging_rows


class StagingIngestTests(unittest.TestCase):
    def test_partial_staging_record_gets_stable_key_and_flags(self):
        rows = [
            {
                "full_name": "Example Person",
                "first_name": "Example",
                "last_name": "Person",
                "source_url": "https://example.gov/roster",
                "pulled_at": "2026-09-13T05:00:00+00:00",
                "charges": [],
            }
        ]

        [(key, payload, snapshot_at)] = prepare_staging_rows(rows)

        self.assertTrue(key.startswith("staging-"))
        self.assertEqual(payload["staging_key"], key)
        self.assertIn("missing_booking_number", payload["quality_flags"])
        self.assertIn("missing_booking_date", payload["quality_flags"])
        self.assertIn("charges_not_provided", payload["quality_flags"])
        self.assertIn("bonds_not_provided", payload["quality_flags"])
        self.assertEqual(snapshot_at, datetime(2026, 9, 13, 5, tzinfo=timezone.utc))

    def test_duplicate_staging_key_is_rejected(self):
        rows = [
            {"booking_number": "A123", "full_name": "One Person"},
            {"booking_number": "A123", "full_name": "Two Person"},
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate staging keys"):
            prepare_staging_rows(rows)


if __name__ == "__main__":
    unittest.main()
