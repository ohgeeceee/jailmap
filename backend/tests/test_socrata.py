"""Tests for the Socrata open-data adapter.

Offline. Socrata portals are the highest-quality source class on JailMap (documented
JSON API, stable identifiers, no scraping), so the mapping rules are worth pinning
down exactly.
"""
import unittest

from backend.adapters.socrata import _iso, map_record

SOURCE = {'state': 'GA', 'county': 'Fulton', 'facility_name': 'Fulton County Jail',
          'source_url': 'https://sharefulton.fultoncountyga.gov/resource/abc1-2345.json'}
PULLED = '2026-09-14T00:00:00+00:00'


class TestSocrataMapper(unittest.TestCase):
    def test_maps_a_standard_record(self):
        row = map_record({
            'booking_number': '2026-00123',
            'last_name': 'DOE',
            'first_name': 'JOHN',
            'booking_date': '2026-09-01T00:00:00.000',
            'charge_description': 'DUI',
            'custody_status': 'In Custody',
            'sex': 'M',
        }, SOURCE, PULLED)
        self.assertIsNotNone(row)
        self.assertEqual(row['booking_number'], '2026-00123')
        self.assertEqual(row['last_name'], 'DOE')
        self.assertEqual(row['first_name'], 'JOHN')
        self.assertEqual(row['status'], 'in_custody')
        self.assertEqual(row['booking_date'], '2026-09-01T00:00:00.000Z')
        self.assertEqual(row['charges'][0]['description'], 'DUI')
        self.assertEqual(row['county'], 'Fulton')

    def test_full_name_only(self):
        row = map_record({'inmate_name': 'SMITH, JANE Q'}, SOURCE, PULLED)
        self.assertEqual(row['full_name'], 'SMITH, JANE Q')
        self.assertEqual(row['first_name'], '')
        self.assertEqual(row['last_name'], '')

    def test_unknown_status_is_not_invented(self):
        row = map_record({'name': 'DOE, JOHN', 'status': 'awaiting classification'},
                         SOURCE, PULLED)
        self.assertIsNone(row['status'])

    def test_record_without_a_name_is_rejected(self):
        self.assertIsNone(map_record({'booking_number': '123', 'sex': 'M'},
                                     SOURCE, PULLED))

    def test_object_values_are_ignored(self):
        # Socrata returns location/point columns as nested objects.
        row = map_record({'name': 'DOE, JOHN',
                          'location': {'latitude': '33.7', 'longitude': '-84.4'},
                          'charge': 'Theft'}, SOURCE, PULLED)
        self.assertIsNotNone(row)
        self.assertEqual(row['charges'][0]['description'], 'Theft')

    def test_date_only_becomes_midday_utc(self):
        row = map_record({'name': 'DOE, JOHN', 'booking_date': '2026-09-01'},
                         SOURCE, PULLED)
        self.assertEqual(row['booking_date'], '2026-09-01T12:00:00Z')

    def test_source_updated_at_falls_back_to_pull_time(self):
        row = map_record({'name': 'DOE, JOHN'}, SOURCE, PULLED)
        self.assertEqual(row['source_updated_at'], PULLED)

    def test_iso_helper(self):
        self.assertEqual(_iso('2026-09-01'), '2026-09-01T12:00:00Z')
        self.assertEqual(_iso('2026-09-01T10:00:00Z'), '2026-09-01T10:00:00Z')
        self.assertIsNone(_iso('not a date'))
        self.assertIsNone(_iso(''))

    def test_charges_empty_when_absent(self):
        row = map_record({'name': 'DOE, JOHN'}, SOURCE, PULLED)
        self.assertEqual(row['charges'], [])


if __name__ == '__main__':
    unittest.main()
