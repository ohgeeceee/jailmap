"""Tests for the Lake County MT jail roster adapter."""
import os
import sys

sys.path.insert(0, "/root/jailmap")

import pytest
from backend.adapters import mt_lake


@pytest.fixture
def sample_pdf_text():
    """Sample text extracted from the Lake County PDF roster."""
    return """Roster Printed on September 15, 2026
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


class TestMtLakeAdapter:
    def test_parse_date(self):
        assert mt_lake._parse_date("08/06/25") == "2025-08-06T12:00:00Z"
        assert mt_lake._parse_date("09/15/2026") == "2026-09-15T12:00:00Z"
        assert mt_lake._parse_date("") is None
        assert mt_lake._parse_date(None) is None

    def test_parse_pdf_with_fixture(self):
        # Can't test PDF parsing without a real PDF, but we can test the regex pattern
        import re
        line = "BEST, DALTON RAY 22-689 20 White Male 406 08/06/25 LCSO"
        m = mt_lake._INMATE_RE.match(line)
        assert m is not None
        assert m.group(1).strip() == "BEST, DALTON RAY"
        assert m.group(2) == "22-689"
        assert m.group(3) == "20"
        assert m.group(4) == "White"
        assert m.group(5) == "Male"
        assert m.group(6) == "406"
        assert m.group(7) == "08/06/25"
        assert m.group(8) == "LCSO"
