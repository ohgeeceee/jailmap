"""Opt-in PostgreSQL invariants; DATABASE_URL must point to an isolated test DB.
Apply schema.sql first; the test transaction rolls back its synthetic rows.
Run: python -m unittest backend.test_integration
"""
import os
import unittest

@unittest.skipUnless(os.environ.get('RECORDS_TEST_DATABASE') == '1', 'Requires isolated PostgreSQL and RECORDS_TEST_DATABASE=1')
class DatabaseTests(unittest.TestCase):
    def test_booking_idempotence_suppression_and_stale_updates(self):
        import psycopg
        from psycopg.rows import dict_row
        from backend.ingest import upsert
        from backend.normalize import normalize
        from backend.test_normalize import fixture
        with psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row) as connection:
            try:
                source = connection.execute("""INSERT INTO records.jurisdictions
                    (state,county,facility_name,source_url,authorization_reference)
                    VALUES ('MT','Synthetic Test',gen_random_uuid()::text,'https://example.gov','test') RETURNING id""").fetchone()
                row = normalize(fixture())
                upsert(connection, source['id'], row)
                upsert(connection, source['id'], row)
                records = connection.execute('SELECT * FROM records.inmates WHERE jurisdiction_id=%s', (source['id'],)).fetchall()
                self.assertEqual(len(records), 1)
                id = records[0]['id']
                self.assertEqual(connection.execute('SELECT count(*) AS n FROM records.bonds WHERE inmate_id=%s', (id,)).fetchone()['n'], 1)
                connection.execute("UPDATE records.inmates SET visibility='suppressed' WHERE id=%s", (id,))
                row['charges'] = []
                upsert(connection, source['id'], row)
                self.assertEqual(connection.execute('SELECT visibility FROM records.inmates WHERE id=%s', (id,)).fetchone()['visibility'], 'suppressed')
                self.assertEqual(connection.execute('SELECT count(*) AS n FROM records.charges WHERE inmate_id=%s', (id,)).fetchone()['n'], 0)
                row['source_updated_at'] = row['booking_date']
                row['first_name'] = 'Stale'
                upsert(connection, source['id'], row)
                self.assertEqual(connection.execute('SELECT first_name FROM records.inmates WHERE id=%s', (id,)).fetchone()['first_name'], 'Example')
            finally:
                connection.rollback()
