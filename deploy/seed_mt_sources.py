"""Register MT counties on jailmap from Montana Blotter's proven sources.

Idempotent: updates existing (state,county,facility_name) rows via
ON CONFLICT. Staging-only by default pending operator review; set
ENABLE=1 to publish straight to the public search (fulton_public style).
"""
import os
import psycopg

MT_SOURCES = [
    # (county, facility, source_url, adapter)
    ('Ravalli',    'Ravalli County Detention Center',        'https://ravalli-so-mt.zuercherportal.com/#/inmates',    'mt_zuercher_staging'),
    ('Gallatin',   'Gallatin County Detention Center',       'https://gallatin-so-mt.zuercherportal.com/#/inmates',   'mt_zuercher_staging'),
    ('Jefferson',  'Jefferson County Jail',                  'https://jefferson-so-mt.zuercherportal.com/#/inmates',  'mt_zuercher_staging'),
    ('Carbon',     'Carbon County Jail',                     'https://carbon-so-mt.zuercherportal.com/#/inmates',     'mt_zuercher_staging'),
    ('Stillwater', 'Stillwater County Jail',                 'https://stillwater-so-mt.zuercherportal.com/#/inmates', 'mt_zuercher_staging'),
    ('Meagher',    'Meagher County Jail',                    'https://meagher-so-mt.zuercherportal.com/#/inmates',    'mt_zuercher_staging'),
    ('Wheatland',  'Wheatland County Jail',                  'https://wheatland-so-mt.zuercherportal.com/#/inmates',  'mt_zuercher_staging'),
    ('Madison',    'Madison County Jail',                    'https://madison-so-mt.zuercherportal.com/#/inmates',    'mt_zuercher_staging'),
]

AUTH = ("Public inmate roster via official county Zuercher portal; "
        "source verified in Montana Blotter production ingestion since 2026.")

ENABLE = os.environ.get('MT_ENABLE', '0') == '1'

SQL = '''
INSERT INTO records.jurisdictions (state, county, facility_name, source_url, adapter,
                                   authorization_reference, enabled, review_status, staging_only)
VALUES ('MT', %s, %s, %s, %s, %s, %s, 'verified', %s)
ON CONFLICT (state, county, facility_name) DO UPDATE SET
    source_url = EXCLUDED.source_url,
    adapter = EXCLUDED.adapter,
    authorization_reference = EXCLUDED.authorization_reference,
    staging_only = EXCLUDED.staging_only
RETURNING id, county, adapter;
'''

conn = psycopg.connect(os.environ['DATABASE_URL'])
with conn.transaction():
    for county, facility, url, adapter in MT_SOURCES:
        row = conn.execute(SQL, (county, facility, url, adapter, AUTH, ENABLE, ENABLE)).fetchone()
        print(row)
conn.close()
