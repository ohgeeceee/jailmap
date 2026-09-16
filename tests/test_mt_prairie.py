"""Tests for the Prairie County MT jail roster adapter."""
import os
import sys

sys.path.insert(0, "/root/jailmap")

import pytest
from backend.adapters import mt_prairie


@pytest.fixture
def sample_html():
    return """
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


class TestMtPrairieAdapter:
    def test_parse_entries(self, sample_html):
        entries = mt_prairie._parse_entries(sample_html)
        assert len(entries) == 1
        entry = entries[0]
        assert entry["first_name"] == "Bryon"
        assert entry["last_name"] == "Fair"
        assert entry["age"] == 30
        assert entry["sex"] == "Male"
        assert entry["race"] == "B"
        assert entry["booking_date"] == "2026-09-14T12:42:00Z"
        assert entry["release_date"] == "2026-09-14T14:15:00Z"
        assert entry["agency"] == "Prairie County Sheriff's Office"
        assert len(entry["charges"]) == 1
        assert entry["charges"][0] == "FAILURE TO APPEAR"

    def test_parse_entries_two_inmates(self, sample_html):
        html = sample_html.replace("_0", "_999").replace("rptListInmates_lblName_0", "rptListInmates_lblName_999")
        entries = mt_prairie._parse_entries(html)
        assert len(entries) == 1

    def test_parse_race_sex_age(self):
        race, sex, age = mt_prairie._parse_race_sex_age("B / M / 30")
        assert race == "B"
        assert sex == "Male"
        assert age == 30

        race, sex, age = mt_prairie._parse_race_sex_age("W / F / 26")
        assert race == "W"
        assert sex == "Female"
        assert age == 26

    def test_parse_date(self):
        assert mt_prairie._parse_date("9/14/2026 12:42:00 PM") == "2026-09-14T12:42:00Z"
        assert mt_prairie._parse_date("10/06/2026 09:00") == "2026-10-06T09:00:00Z"
        assert mt_prairie._parse_date("") is None
        assert mt_prairie._parse_date(None) is None
