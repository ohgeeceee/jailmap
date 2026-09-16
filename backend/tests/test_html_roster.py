"""Tests for the generic HTML roster parser.

Offline fixtures only — no network. The parser exists so 70+ bespoke county sites
do not each need their own adapter, so the parsing rules are the product here and
are worth pinning down precisely.
"""
import unittest

from backend.adapters.html_roster import parse_html, _parse_date, _parse_amount


SOURCE = {'state': 'MT', 'county': 'Example', 'facility_name': 'Example County Jail',
          'source_url': 'https://example.gov/roster'}


def table(headers, rows):
    head = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''.join(
        '<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in rows
    )
    return f'<html><body><table><tr>{head}</tr>{body}</table></body></html>'


class TestHtmlRoster(unittest.TestCase):
    def test_parses_a_standard_roster(self):
        html = table(
            ['Name', 'Booking Number', 'Booking Date', 'Charges', 'Bond', 'Status'],
            [['DOE, JOHN A', '2026-001', '2026-09-01', 'DUI', '$1,500.00', 'In Custody']],
        )
        rows = parse_html(html, SOURCE)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['last_name'], 'DOE')
        self.assertEqual(row['first_name'], 'JOHN')
        self.assertEqual(row['booking_number'], '2026-001')
        self.assertEqual(row['booking_date'], '2026-09-01T12:00:00Z')
        self.assertEqual(row['status'], 'in_custody')
        self.assertEqual(row['bonds'][0]['amount'], 1500.0)
        self.assertEqual(row['charges'][0]['description'], 'DUI')
        self.assertEqual(row['county'], 'Example')

    def test_first_last_columns_without_full_name(self):
        html = table(['Last Name', 'First Name', 'Booking Date'],
                     [['SMITH', 'JANE', '09/04/2026']])
        rows = parse_html(html, SOURCE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['last_name'], 'SMITH')
        self.assertEqual(rows[0]['first_name'], 'JANE')
        self.assertEqual(rows[0]['booking_date'], '2026-09-04T12:00:00Z')

    def test_table_without_identity_is_ignored(self):
        # A stats table (population, capacity) must never be read as people.
        html = table(['Facility', 'Population', 'Capacity'], [['Main', '120', '150']])
        self.assertEqual(parse_html(html, SOURCE), [])

    def test_status_is_not_invented_when_absent(self):
        html = table(['Name', 'Booking Date'], [['DOE, JOHN', '2026-09-01']])
        rows = parse_html(html, SOURCE)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['status'])

    def test_repeated_header_row_is_dropped(self):
        inner = ('<tr><th>Name</th><th>Booking Date</th></tr>'
                 '<tr><td>DOE, JOHN</td><td>2026-09-01</td></tr>'
                 '<tr><td>Name</td><td>Booking Date</td></tr>')
        html = f'<html><body><table>{inner}</table></body></html>'
        rows = parse_html(html, SOURCE)
        self.assertEqual(len(rows), 1)

    def test_short_rows_are_skipped(self):
        html = table(['Name', 'Booking Number', 'Booking Date'],
                     [['DOE, JOHN', '2026-001']])
        self.assertEqual(parse_html(html, SOURCE), [])

    def test_unknown_status_falls_back_to_none(self):
        html = table(['Name', 'Status'], [['DOE, JOHN', 'Awaiting classification']])
        rows = parse_html(html, SOURCE)
        self.assertIsNone(rows[0]['status'])

    def test_multiple_tables(self):
        html = (table(['Name', 'Booking Date'], [['ONE, A', '2026-09-01']])
                + table(['Name', 'Booking Date'], [['TWO, B', '2026-09-02']]))
        self.assertEqual(len(parse_html(html, SOURCE)), 2)

    def test_date_parsing(self):
        self.assertEqual(_parse_date('2026-09-01'), '2026-09-01T12:00:00Z')
        self.assertEqual(_parse_date('9/1/2026'), '2026-09-01T12:00:00Z')
        self.assertIsNone(_parse_date('sometime'))
        self.assertIsNone(_parse_date(''))
        self.assertIsNone(_parse_date('13/45/2026'))

    def test_amount_parsing(self):
        self.assertEqual(_parse_amount('$1,500.00'), 1500.0)
        self.assertEqual(_parse_amount('2500'), 2500.0)
        self.assertIsNone(_parse_amount('no bond'))
        self.assertIsNone(_parse_amount(''))

    def test_html_is_unescaped_and_whitespace_collapsed(self):
        html = ('<table><tr><th>Name</th><th>Charges</th></tr>'
                '<tr><td>O&#39;BRIEN,   PAT</td><td>Theft&nbsp;&amp;&nbsp;fraud</td></tr></table>')
        rows = parse_html(html, SOURCE)
        self.assertEqual(rows[0]['last_name'], "O'BRIEN")
        self.assertIn('fraud', rows[0]['charges'][0]['description'])


if __name__ == '__main__':
    unittest.main()
