import os
import unittest

@unittest.skipUnless(os.environ.get('RECORDS_TEST_DATABASE')=='1','Requires isolated PostgreSQL')
class HierarchyTests(unittest.TestCase):
    def test_cross_state_jails_and_sources_are_rejected(self):
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL']) as c:
            try:
                for id,name,code,fips in [('test-mt','Montana','MT','30'),('test-ga','Georgia','GA','13')]:
                    c.execute('''INSERT INTO public."State"(id,name,abbrev,"fipsCode","updatedAt") VALUES (%s,%s,%s,%s,now())''',(id,name,code,fips))
                c.execute('''INSERT INTO public."County"(id,name,"fipsCode","stateId","updatedAt") VALUES ('test-county','Synthetic','30001','test-mt',now())''')
                with self.assertRaises(psycopg.IntegrityError):
                    with c.transaction():
                        c.execute('''INSERT INTO public."Jail"(id,name,"countyId","stateId","updatedAt") VALUES ('test-jail','Synthetic','test-county','test-ga',now())''')
                with self.assertRaises(psycopg.errors.RaiseException):
                    with c.transaction():
                        c.execute('''INSERT INTO records.jurisdictions(state,county,county_id,facility_name,source_url,authorization_reference)
                          VALUES ('GA','Synthetic','test-county','Synthetic','https://example.gov','test')''')
                with self.assertRaises(psycopg.IntegrityError):
                    with c.transaction():
                        c.execute('''INSERT INTO records.jurisdictions(state,county,facility_name,source_url,authorization_reference,enabled,staging_only)
                          VALUES ('MT','Synthetic','Synthetic','https://example.gov','test',true,true)''')
            finally: c.rollback()

if __name__=='__main__': unittest.main()
