"""Tests for Beaverhead and Lewis and Clark PDF adapters."""
import os
import sys
import unittest

sys.path.insert(0, "/root/jailmap")

from backend.adapters import mt_beaverhead, mt_lewis_and_clark


class TestMtBeaverheadAdapter(unittest.TestCase):
    def test_inmate_header_regex(self):
        line = "Book#: 26BK00095 Name: AMOS,NICHOLASC NameID: 21693 Rel.Dt: **/**/**"
        m = mt_beaverhead._INMATE_HEADER_RE.search(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "26BK00095")
        self.assertEqual(m.group(2), "AMOS,NICHOLASC")
        self.assertEqual(m.group(3), "21693")

    def test_statute_regex(self):
        line = "45-5-215(2)(a)[1st] StrangulationofPartnerorFamily BCSO DC-1-2026- 03/09/26 189"
        m = mt_beaverhead._STATUTE_RE.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "45-5-215(2)(a)[1st]")
        self.assertIn("Strangulation", m.group(2))
        self.assertEqual(m.group(5), "03/09/26")

    def test_parse_date(self):
        self.assertEqual(mt_beaverhead._parse_date("03/09/26"), "2026-03-09T12:00:00Z")
        self.assertEqual(mt_beaverhead._parse_date("**/**/**"), None)
        self.assertEqual(mt_beaverhead._parse_date(""), None)
        self.assertEqual(mt_beaverhead._parse_date(None), None)


class TestMtLewisAndClarkAdapter(unittest.TestCase):
    def test_inmate_regex(self):
        line = "ALDEN, BRANDON 42 Male 09/09/26 01:31 26-01659 Charge: 45-7-302(1)"
        m = mt_lewis_and_clark._INMATE_RE.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "ALDEN, BRANDON")
        self.assertEqual(m.group(2), "42")
        self.assertEqual(m.group(3), "Male")
        self.assertEqual(m.group(6), "26-01659")

    def test_parse_datetime(self):
        result = mt_lewis_and_clark._parse_datetime("09/09/26", "01:31")
        self.assertEqual(result, "2026-09-09T01:31:00Z")
        self.assertIsNone(mt_lewis_and_clark._parse_datetime("", ""))
        self.assertIsNone(mt_lewis_and_clark._parse_datetime(None, None))


if __name__ == "__main__":
    unittest.main()
