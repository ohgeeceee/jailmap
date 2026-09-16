"""Tests for the Lake County MT jail roster adapter."""
import os
import sys
import unittest

sys.path.insert(0, "/root/jailmap")

from backend.adapters import mt_lake


SAMPLE_PDF_TEXT = """Roster Printed on September 15, 2026
Last, First Middle Name Jacket # Age Race Sex Days Booking Date Arr Agency Charges / Hold Reasons
45-5-502(3) - Sexual Assault Felony Inflicts Bodily Injury or Victim is Less than 16
BEST, DALTON RAY 22-689 20 White Male 406 08/06/25 LCSO Offender 3 Years Older
45-6-101(1)[2] - Criminal Mischief Pecuniary Loss More Than $1,500
BITSINNI, ORLI CHRISTENSON 18-3228 27 American Male 219 02/09/26 LCSO 46-23-1012 - Probation And Parole Detention For Probation Violation
45-5-215(2)(a)[1st] - Strangulation of Partner or Family Member - 1st Offense
45-9-102[Fel] - Criminal Possession Of Dangerous Drugs - Not Otherwise Provided For
BLACK, LEROY DENNIS 18-000152 35 American Male 30 08/17/26 LCSO in Subsection 45-9-102(1) or (2)
45-5-503(5) - Sexual Intercourse Without Consent Victim is 14 or Older and Offender is
BURGESS, KEEYON MICHAEL 26-015204 18 White Male 11 09/05/26 LCSO 18 or Less
46-23-1012 - Probation And Parole Detention For Probation Violation
BURKE, MATTHEW JAMES 26-015206 31 Unknown Male 10 09/06/26 LCSO 45-9-102[Fel] - Criminal Possession Of Dangerous Drugs - Not Otherwise Provided For
in Subsection 45-9-102(1) or (2)
"""


class TestMtLakeAdapter(unittest.TestCase):
    def test_parse_date_short_year(self):
        self.assertEqual(mt_lake._parse_date("08/06/25"), "2025-08-06T12:00:00Z")

    def test_parse_date_long_year(self):
        self.assertEqual(mt_lake._parse_date("09/15/2026"), "2026-09-15T12:00:00Z")

    def test_parse_date_empty(self):
        self.assertIsNone(mt_lake._parse_date(""))
        self.assertIsNone(mt_lake._parse_date(None))

    def test_inmate_regex(self):
        line = "BEST, DALTON RAY 22-689 20 White Male 406 08/06/25 LCSO"
        m = mt_lake._INMATE_RE.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).strip(), "BEST, DALTON RAY")
        self.assertEqual(m.group(2), "22-689")
        self.assertEqual(m.group(3), "20")
        self.assertEqual(m.group(4), "White")
        self.assertEqual(m.group(5), "Male")
        self.assertEqual(m.group(6), "406")
        self.assertEqual(m.group(7), "08/06/25")
        self.assertEqual(m.group(8), "LCSO")

    def test_inmate_regex_no_match(self):
        line = "Charges / Hold Reasons"
        m = mt_lake._INMATE_RE.match(line)
        self.assertIsNone(m)


if __name__ == "__main__":
    unittest.main()
