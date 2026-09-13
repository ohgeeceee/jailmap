"""Transactional runner tests; requires a disposable DB with current migrations."""
import os
import unittest
from unittest.mock import patch

@unittest.skipUnless(os.environ.get('RECORDS_TEST_DATABASE')=='1','Requires isolated PostgreSQL')
class RunnerTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool
        from backend.normalize import normalize
        from backend.test_normalize import fixture
        self.connection=psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row,autocommit=True)
        self.source=self.connection.execute('''INSERT INTO records.jurisdictions(state,county,facility_name,source_url,
            adapter,authorization_reference,review_status,staging_only)
            VALUES ('GA','Synthetic',gen_random_uuid()::text,'https://example.gov','test_staging','synthetic test','verified',true)
            RETURNING id''').fetchone()['id']
        self.row=normalize(fixture())
        self.pool=ConnectionPool(os.environ['DATABASE_URL'],min_size=1,max_size=3,kwargs={'row_factory':dict_row},open=False)

    def tearDown(self):
        self.connection.execute('DELETE FROM records.inmates WHERE jurisdiction_id=%s',(self.source,))
        for table in ['staged_bookings','ingestion_runs']:
            self.connection.execute(f'DELETE FROM records.{table} WHERE jurisdiction_id=%s',(self.source,))
        self.connection.execute('DELETE FROM records.jurisdictions WHERE id=%s',(self.source,))
        self.connection.close()

    def invoke(self,rows,dry_run=False):
        from backend import ingest
        with patch.object(ingest,'pool',self.pool),patch.dict(ingest.ADAPTERS,{'test_staging':lambda _:rows,'fulton_public_roster':lambda _:rows}):
            ingest.run(jurisdiction=self.source,dry_run=dry_run)

    def count(self,table):
        return self.connection.execute(f'SELECT count(*) AS n FROM records.{table} WHERE jurisdiction_id=%s',(self.source,)).fetchone()['n']

    def test_dry_run_has_no_writes(self):
        self.invoke([self.row],True)
        self.assertEqual(self.count('staged_bookings'),0)
        self.assertEqual(self.count('ingestion_runs'),0)
        self.assertEqual(self.count('inmates'),0)

    def test_staging_never_publishes(self):
        self.invoke([self.row])
        self.assertEqual(self.count('staged_bookings'),1)
        self.assertEqual(self.count('inmates'),0)
        run=self.connection.execute('SELECT status,record_count FROM records.ingestion_runs WHERE jurisdiction_id=%s',(self.source,)).fetchone()
        self.assertEqual(run,{'status':'success','record_count':1})

    def test_duplicate_snapshot_rolls_back_and_records_failure(self):
        with self.assertRaises(SystemExit): self.invoke([self.row,self.row])
        self.assertEqual(self.count('staged_bookings'),0)
        run=self.connection.execute('SELECT status FROM records.ingestion_runs WHERE jurisdiction_id=%s',(self.source,)).fetchone()
        self.assertEqual(run['status'],'failed')

    def test_complete_public_snapshot_hides_absent_without_claiming_release(self):
        from backend.ingest import upsert
        self.connection.execute("UPDATE records.jurisdictions SET staging_only=false,enabled=true,adapter='fulton_public_roster' WHERE id=%s",(self.source,))
        old={**self.row,'booking_number':'OLDER-SYNTHETIC'}
        upsert(self.connection,self.source,old)
        self.row['observed_at']=self.row['source_updated_at']
        self.invoke([self.row])
        rows=self.connection.execute('SELECT booking_number,visibility,observed_at FROM records.inmates WHERE jurisdiction_id=%s',(self.source,)).fetchall()
        by_key={r['booking_number']:r for r in rows}
        self.assertEqual(by_key['OLDER-SYNTHETIC']['visibility'],'unlisted')
        self.assertEqual(by_key[self.row['booking_number']]['visibility'],'public')
        self.assertEqual(by_key[self.row['booking_number']]['observed_at'],self.row['source_updated_at'])

if __name__=='__main__': unittest.main()
