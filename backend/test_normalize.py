import unittest
from copy import deepcopy
from decimal import Decimal
from backend.normalize import normalize

def fixture():
    return {'booking_number':'EXAMPLE-001','first_name':' Example ', 'last_name':'Person',
        'booking_date':'2025-01-01T12:00:00Z', 'updated_at':'2025-01-02T12:00:00Z',
        'status':'in_custody', 'charges':[{'id':'c1','description':'Synthetic example charge'}],
        'bonds':[{'id':'b1','amount':'100.10','type':'cash','status':'set'}]}

class NormalizationTests(unittest.TestCase):
    def test_money_preserves_cents_and_names_trim(self):
        row = normalize(fixture())
        self.assertEqual(row['bonds'][0]['amount'], Decimal('100.10'))
        self.assertEqual(row['first_name'], 'Example')

    def test_unknown_bond_is_not_zero(self):
        row = fixture(); row['bonds'][0]['amount'] = None
        self.assertIsNone(normalize(row)['bonds'][0]['amount'])

    def test_bad_money_rejected(self):
        for value in ('NaN', 'Infinity', '-1', '0.001', '1000000000000'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                row = fixture(); row['bonds'][0]['amount'] = value; normalize(row)

    def test_timezone_required(self):
        row = fixture(); row['booking_date'] = '2025-01-01T12:00:00'
        with self.assertRaises(ValueError): normalize(row)

    def test_missing_collection_is_not_empty_snapshot(self):
        row = fixture(); del row['charges']
        with self.assertRaises(ValueError): normalize(row)

    def test_duplicate_child_rejected(self):
        row = fixture(); row['charges'].append(deepcopy(row['charges'][0]))
        with self.assertRaises(ValueError): normalize(row)

    def test_explicit_release(self):
        row = fixture(); row['status'] = 'released'
        self.assertEqual(normalize(row)['visibility'], 'released')

    def test_missing_identity_key_rejected(self):
        row = fixture(); del row['booking_number']
        with self.assertRaises(ValueError): normalize(row)

if __name__ == '__main__': unittest.main()
