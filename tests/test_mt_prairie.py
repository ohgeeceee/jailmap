"""Tests for the Prairie County MT jail roster adapter."""
import os
import sys
import unittest

sys.path.insert(0, "/root/jailmap")

from backend.adapters import mt_prairie


SAMPLE_HTML = """
<html>
<body>
<form method="post" action="./NewInmates.aspx" id="form1">
<span id="lblAgencyName" class="Headerfont"><b>Prairie County Sheriffs Office</b></span>
<span id="lblPageDescription" class="Headerfont"><b>Inmates Booked in Last 48 Hours</b></span>
<span id="lblInmateslisted" class="Headerfont"><b>8 inmates shown out of 8 total</b></span>

<a id="ContentPlaceHolder1_rptListInmates_lnkName_0" name="Fair, Bryon Steven"></a>
<img id="ContentPlaceHolder1_rptListInmates_imgPhoto_0" src="GetPhoto6.aspx?OurImageID=26599913" alt="Fair, Bryon Steven" width="150" />
<span id="ContentPlaceHolder1_rptListInmates_lblName_0" class="tableHeading">Fair, Bryon Steven</span>
<span id="ContentPlaceHolder1_rptListInmates_lblRace_0">B / M / 30         years</span>
<span id="ContentPlaceHolder1_rptListInmates_lblAddress_0">Scott, AR</span>
<b>Arrested:</b>    <span id="ContentPlaceHolder1_rptListInmates_lblArrestDate_0">9/14/2026 12:42:00 PM</span>
<b>Arrested By:</b>    <span id="ContentPlaceHolder1_rptListInmates_lblArrestBy_0">Prairie County Sheriff's Office</span>
<span id="ContentPlaceHolder1_rptListInmates_lblRelease_0"><b>Released:</b></span>
<span id="ContentPlaceHolder1_rptListInmates_lblReleaseDate_0">9/14/2026 2:15:00 PM</span>

<tr id="ContentPlaceHolder1_rptListInmates_tblCharges_0" name="tblCharges">
<table cellspacing="0" cellpadding="3" rules="cols" id="ContentPlaceHolder1_rptListInmates_chargeGrid_0">
<tr bgcolor="LightGrey"><th scope="col"><font color="Black"><b>Charges</b></font></th></tr>
<tr><td width="400"><font color="Black"><span id="ContentPlaceHolder1_rptListInmates_chargeGrid_0_Label1_0">FAILURE TO APPEAR - FELONY</span></font></td></tr>
<tr bgcolor="#CCCCCC"><td width="400"><font color="Black"><span id="ContentPlaceHolder1_rptListInmates_chargeGrid_0_Label1_1">FAILURE TO APPEAR</span></font></td></tr>
</table>
</tr>

</form>
</body>
</html>
"""


class TestMtPrairieAdapter(unittest.TestCase):
    def test_parse_entries(self):
        entries = mt_prairie._parse_entries(SAMPLE_HTML)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["first_name"], "Bryon Steven")
        self.assertEqual(entry["last_name"], "Fair")
        self.assertEqual(entry["age"], 30)
        self.assertEqual(entry["sex"], "Male")
        self.assertEqual(entry["race"], "B")
        self.assertEqual(entry["booking_date"], "2026-09-14T12:42:00Z")
        self.assertEqual(entry["release_date"], "2026-09-14T14:15:00Z")
        self.assertEqual(entry["agency"], "Prairie County Sheriff's Office")
        self.assertEqual(len(entry["charges"]), 1)
        self.assertEqual(entry["charges"][0], "FAILURE TO APPEAR")

    def test_parse_race_sex_age_male(self):
        race, sex, age = mt_prairie._parse_race_sex_age("B / M / 30")
        self.assertEqual(race, "B")
        self.assertEqual(sex, "Male")
        self.assertEqual(age, 30)

    def test_parse_race_sex_age_female(self):
        race, sex, age = mt_prairie._parse_race_sex_age("W / F / 26")
        self.assertEqual(race, "W")
        self.assertEqual(sex, "Female")
        self.assertEqual(age, 26)

    def test_parse_race_sex_age_empty(self):
        race, sex, age = mt_prairie._parse_race_sex_age("")
        self.assertIsNone(race)
        self.assertIsNone(sex)
        self.assertIsNone(age)

    def test_parse_date_full(self):
        self.assertEqual(mt_prairie._parse_date("9/14/2026 12:42:00 PM"), "2026-09-14T12:42:00Z")

    def test_parse_date_short(self):
        self.assertEqual(mt_prairie._parse_date("10/06/2026 09:00 AM"), "2026-10-06T09:00:00Z")

    def test_parse_date_empty(self):
        self.assertIsNone(mt_prairie._parse_date(""))
        self.assertIsNone(mt_prairie._parse_date(None))


if __name__ == "__main__":
    unittest.main()
