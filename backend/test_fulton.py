import unittest
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from backend.fulton import snapshot_time,convert,fetch,fetch_public,URL

class FultonTests(unittest.TestCase):
    def test_publication_mode_is_rejected_without_fetching(self):
        with self.assertRaises(ValueError): fetch({'source_url':URL,'staging_only':False})

    def test_source_observation_is_previous_evening(self):
        now=datetime(2026,9,7,10,tzinfo=timezone.utc)
        result=snapshot_time(datetime(2026,9,7,8,tzinfo=timezone.utc).timestamp(),now)
        self.assertEqual(result,datetime(2026,9,6,23,30,tzinfo=timezone.utc))
        with self.assertRaises(ValueError): snapshot_time((now-timedelta(days=3)).timestamp(),now)
        with self.assertRaises(ValueError): snapshot_time((now+timedelta(hours=1)).timestamp(),now)

    def test_staging_preserves_unknown_information(self):
        observed=datetime(2025,9,6,23,30,tzinfo=timezone.utc)
        result=convert({'name':'SAMPLE, EXAMPLE MIDDLE','bookingnbr':'TEST-001','bookingdate':'2025-09-01T00:00:00'},observed)
        self.assertEqual(result['booking_date_precision'],'date')
        self.assertFalse(result['charges_provided'])
        self.assertFalse(result['bonds_provided'])
        self.assertIn('age',result['unavailable_fields'])
        self.assertEqual(result['eligibility_basis'],'official_named_public_roster')
        self.assertEqual(result['observed_at'],observed)

    def test_unexpected_name_and_date_fail_closed(self):
        observed=datetime(2025,9,6,23,30,tzinfo=timezone.utc)
        with self.assertRaises(ValueError): convert({'name':'UNSTRUCTURED'},observed)
        result=convert({'name':'SAMPLE, EXAMPLE','bookingnbr':'TEST','bookingdate':'2025-09-09T00:00:00'},observed)
        self.assertIn('booking_after_stated_snapshot',result['publication_blockers'])

    def test_public_roster_withholds_bad_dates_and_redactions(self):
        observed=datetime(2025,9,6,23,30,tzinfo=timezone.utc)
        row=convert({'name':'SAMPLE, EXAMPLE','bookingnbr':'TEST-001','bookingdate':'2025-09-01T00:00:00'},observed)
        rows=[row,{**row,'publication_blockers':['booking_after_stated_snapshot']},{**row,'first_name':'REDACTED'}]
        with patch('backend.fulton.fetch',return_value=rows):
            self.assertEqual(fetch_public({'adapter':'fulton_public_roster','staging_only':False}),[row])

if __name__=='__main__': unittest.main()
