"""Generate a repeatable geography/ingestion-queue migration from Census 2025 ZIPs.

python -m backend.national_seed > deploy/national-seed.sql
Run SQL as the database owner, with psql -v ON_ERROR_STOP=1.
No facility or booking is invented from a county's existence.
"""
import csv
import io
import zipfile
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[1] / 'data' / 'reference'
STATES = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())

def read_zip(name):
    with zipfile.ZipFile(REFERENCE / name) as archive:
        text = archive.read(archive.namelist()[0]).decode('utf-8-sig')
    return list(csv.DictReader(io.StringIO(text), delimiter='|'))

def literal(value):
    return "'" + value.replace("'", "''") + "'"

def generate():
    states = [r for r in read_zip('states.zip') if r['USPS'] in STATES]
    counties = [r for r in read_zip('counties.zip') if r['USPS'] in STATES]
    assert {r['USPS'] for r in states} == STATES and len(states) == 50
    assert len({r['GEOID'] for r in counties}) == len(counties) > 3100
    assert sum(r['USPS'] == 'MT' for r in counties) == 56
    assert all(len(r['GEOID']) == 5 and r['GEOID'].isdigit() for r in counties)
    yield 'BEGIN;'
    yield '''CREATE TABLE IF NOT EXISTS records.county_ingestion_queue (
      county_id text PRIMARY KEY REFERENCES public."County"(id),
      status text NOT NULL DEFAULT 'source_discovery' CHECK (status IN
        ('source_discovery','adapter_needed','testing','active','blocked','no_local_jail')),
      source_url text, adapter text, notes text NOT NULL DEFAULT '',
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS records.ingestion_runs (
      id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      jurisdiction_id uuid NOT NULL REFERENCES records.jurisdictions(id),
      started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
      status text NOT NULL CHECK (status IN ('running','success','failed','dry_run')),
      record_count integer, error_type text
    );
    CREATE INDEX IF NOT EXISTS ingestion_runs_source_time ON records.ingestion_runs(jurisdiction_id,started_at DESC);
    ALTER TABLE records.jurisdictions ADD COLUMN IF NOT EXISTS jail_id text REFERENCES public."Jail"(id);
    ALTER TABLE records.jurisdictions ADD COLUMN IF NOT EXISTS review_status text NOT NULL DEFAULT 'unverified';
    GRANT SELECT,INSERT,UPDATE,DELETE ON records.county_ingestion_queue,records.ingestion_runs TO jailmap_app;
    GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA records TO jailmap_app;'''
    for r in states:
        values = ','.join(literal(v) for v in ('state-'+r['GEOID'],r['NAME'],r['USPS'],r['GEOID']))
        yield f'''INSERT INTO public."State"(id,name,abbrev,"fipsCode","updatedAt") VALUES ({values},now())
          ON CONFLICT (abbrev) DO UPDATE SET name=EXCLUDED.name,"fipsCode"=EXCLUDED."fipsCode","updatedAt"=now();'''
    for r in counties:
        values = ','.join(literal(v) for v in ('county-'+r['GEOID'],r['NAME'],r['GEOID']))
        yield f'''INSERT INTO public."County"(id,name,"fipsCode","stateId","updatedAt")
          SELECT {values},id,now() FROM public."State" WHERE abbrev={literal(r['USPS'])}
          ON CONFLICT ("fipsCode") DO UPDATE SET name=EXCLUDED.name,"stateId"=EXCLUDED."stateId","updatedAt"=now();'''
        yield f'''INSERT INTO records.county_ingestion_queue(county_id)
          SELECT id FROM public."County" WHERE "fipsCode"={literal(r['GEOID'])} ON CONFLICT DO NOTHING;'''
    yield '''DO $$ BEGIN
      IF to_regclass('records.state_ingestion_status') IS NULL THEN
      EXECUTE $view$CREATE VIEW records.state_ingestion_status AS
      SELECT s.abbrev,s.name,count(DISTINCT c.id) AS counties,
        count(DISTINCT j.id) AS facilities,
        count(DISTINCT r.id) FILTER (WHERE r.enabled) AS enabled_sources,
        count(DISTINCT q.county_id) FILTER (WHERE q.status='source_discovery') AS counties_needing_discovery
      FROM public."State" s LEFT JOIN public."County" c ON c."stateId"=s.id
      LEFT JOIN public."Jail" j ON j."countyId"=c.id
      LEFT JOIN records.jurisdictions r ON r.jail_id=j.id
      LEFT JOIN records.county_ingestion_queue q ON q.county_id=c.id
      GROUP BY s.id,s.abbrev,s.name$view$;
      END IF;
      END $$;
      GRANT SELECT ON records.state_ingestion_status TO jailmap_app;
      COMMIT;'''

if __name__ == '__main__':
    print('\n'.join(generate()))
