import unittest
from unittest.mock import patch

from backend.adapters import gov_website


SOURCE = {
    "state": "AR",
    "county": "Example",
    "facility_name": "Example County Jail",
    "source_url": "https://example.gov/inmate-roster/filters/current/booking_time=desc/1",
}


def roster_row(number="A-1", age="30", booking_date="09-19-2026 5:30 PM", name="DOE, JOHN"):
    return f'''<div class="roster_name">{name}</div>
      <div><div class="inmate_data_bold"><strong>Booking #:</strong></div>
      <div class="inmate_data_content">{number}</div></div>
      <div><div class="inmate_data_bold"><strong>Age:</strong></div>
      <div class="inmate_data_content">{age}</div></div>
      <div><div class="inmate_data_bold"><strong>Booking Date:</strong></div>
      <div class="inmate_data_content">{booking_date}</div></div>
      <div><div class="inmate_data_bold"><strong>Charges:</strong></div>
      <div class="inmate_data_content">Example charge</div></div>
      <img src="https://storage.googleapis.com/example/mugshot.jpg">'''


class GovernmentWebsiteAdapterTests(unittest.TestCase):
    def test_parses_adult_without_collecting_mugshot(self):
        [row] = gov_website._parse_roster_page(roster_row(), SOURCE)
        self.assertEqual(row["booking_number"], "A-1")
        self.assertEqual(row["booking_date"], "2026-09-19T17:30:00-05:00")
        self.assertIsNone(row["mugshot_url"])

    def test_excludes_minor_and_fails_when_age_is_unknown(self):
        self.assertEqual(gov_website._parse_roster_page(roster_row(age="17"), SOURCE), [])
        with self.assertRaisesRegex(ValueError, "adult-eligibility"):
            gov_website._parse_roster_page(roster_row(age="Unknown"), SOURCE)

    def test_requires_booking_identity_and_real_date(self):
        with self.assertRaisesRegex(ValueError, "stable booking number"):
            gov_website._parse_roster_page(roster_row(number=""), SOURCE)
        with self.assertRaisesRegex(ValueError, "stable booking number"):
            gov_website._parse_roster_page(roster_row(booking_date="Not a date"), SOURCE)

    def test_fetch_uses_first_response_once_and_requires_later_pages(self):
        first = (roster_row() +
                 '<a href="/inmate-roster/filters/current/booking_time=desc/2">2</a>').encode()
        second = roster_row(number="A-2", name="SMITH, JANE").encode()
        with patch.object(gov_website, "_assert_authorized"), \
                patch.object(gov_website, "_fetch_html", side_effect=[first, second]) as fetch:
            rows = gov_website.fetch(SOURCE)
        self.assertEqual([row["booking_number"] for row in rows], ["A-1", "A-2"])
        self.assertEqual(fetch.call_count, 2)

        with patch.object(gov_website, "_assert_authorized"), \
                patch.object(gov_website, "_fetch_html", side_effect=[first, RuntimeError("offline")]):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                gov_website.fetch(SOURCE)

    def test_rejects_duplicate_booking_numbers(self):
        first = (roster_row() +
                 '<a href="/inmate-roster/filters/current/booking_time=desc/2">2</a>').encode()
        with patch.object(gov_website, "_assert_authorized"), \
                patch.object(gov_website, "_fetch_html", side_effect=[first, roster_row().encode()]):
            with self.assertRaisesRegex(ValueError, "Duplicate booking numbers"):
                gov_website.fetch(SOURCE)


if __name__ == "__main__":
    unittest.main()
