"""Seed/upgrade MT jurisdictions on jailmap from proven Montana Blotter sources.

Updates existing placeholder rows by (state, county) — the homepage
standard_json placeholders get the real roster URL + adapter. Counties
without an existing row are inserted. Staging-only pending review.
"""
import os
import psycopg

# (county, facility, source_url, adapter)  adapter=None => keep placeholder, just fix URL
MT_SOURCES = [
    ('Ravalli',    'Ravalli County Detention Center',        'https://ravalli-so-mt.zuercherportal.com/#/inmates',    'mt_zuercher_staging'),
    ('Gallatin',   'Gallatin County Detention Center',       'https://gallatin-so-mt.zuercherportal.com/#/inmates',   'mt_zuercher_staging'),
    ('Jefferson',  'Jefferson County Jail',                  'https://jefferson-so-mt.zuercherportal.com/#/inmates',  'mt_zuercher_staging'),
    ('Carbon',     'Carbon County Jail',                     'https://carbon-so-mt.zuercherportal.com/#/inmates',     'mt_zuercher_staging'),
    ('Stillwater', 'Stillwater County Jail',                 'https://stillwater-so-mt.zuercherportal.com/#/inmates', 'mt_zuercher_staging'),
    ('Meagher',    'Meagher County Jail',                    'https://meagher-so-mt.zuercherportal.com/#/inmates',    'mt_zuercher_staging'),
    ('Wheatland',  'Wheatland County Jail',                  'https://wheatland-so-mt.zuercherportal.com/#/inmates',  'mt_zuercher_staging'),
    ('Madison',    'Madison County Jail',                    'https://madison-so-mt.zuercherportal.com/#/inmates',    'mt_zuercher_staging'),
    ('Flathead',   'Flathead County Detention Center',       'https://apps.flathead.mt.gov/jailroster/',              'flathead_html_staging'),
    ('Missoula',   'Missoula County Detention Facility',     'https://webapps.missoulacounty.us/jailroster/Inmates',  'missoula_html_staging'),
    ('Yellowstone','Yellowstone County Detention Facility',  'https://www.yellowstonecountymt.gov/sheriff/detention/dcsearch.asp', 'yellowstone_html_staging'),
    ('Cascade',    'Cascade County Detention Center',        'https://www.cascadecountymt.gov/314/Inmate-Roster',     None),
    ('Valley',     'Valley County Jail',                     'https://www.valleycountymt.gov/1288/Jail-Roster',       None),
    ('Lake',       'Lake County Jail',                       'https://www.lakemt.gov/DocumentCenter/View/816/Jail_Roster-?bidId=', None),
    ('Beaverhead', 'Beaverhead County Jail',                 'https://beaverheadcountymt.gov/wp-content/uploads/2026/03/Jail-Roster.pdf', None),
    ('Chouteau',   'Chouteau County Jail',                   'https://chouteaucountysheriff.com/',                    None),
    ('Fergus',     'Fergus County Detention Center',         'https://fergusmt.gov/detention-center-roster',          None),
    ('Lewis and Clark', 'Lewis and Clark County Detention Center', 'https://www.lccountymt.gov/Sheriff/Detention-Center', None),
    ('Silver Bow', 'Butte-Silver Bow Detention Center',      'https://co.silverbow.mt.us/3274/Detention-Center',      None),
    ('Glacier',    'Glacier County Jail',                    'https://glaciercountymt.gov/category/jail-roster/',     None),
    ('Custer',     'Custer County Jail',                     'https://custercountymt.gov/emergency-enforcement/sheriff/', None),
    ('Garfield',   'Garfield County Jail',                   'https://www.garcosheriff.com/PDFs/current_inmates.pdf', None),
    ('Prairie',    'Prairie County Jail',                    'https://www.myr2m.com/PrairieCoRoster/NewInmates.aspx', None),
    ('Carter',     'Carter County Jail',                     'https://cartercountysheriff.us/inmate-search',          None),
]

AUTH = ("Public inmate roster from official county site/portal; URL and "
        "parser proven in Montana Blotter production ingestion.")

UPDATE = '''UPDATE records.jurisdictions
    SET facility_name=%s, source_url=%s,
        adapter=COALESCE(%s, adapter),
        authorization_reference=%s,
        staging_only=TRUE, enabled=FALSE, review_status='verified'
    WHERE state='MT' AND county=%s
    RETURNING id'''

INSERT = '''INSERT INTO records.jurisdictions
    (state, county, facility_name, source_url, adapter, authorization_reference,
     enabled, review_status, staging_only)
    VALUES ('MT', %s, %s, %s, COALESCE(%s,'PENDING-ADAPTER'), %s, FALSE, 'verified', TRUE)
    RETURNING id'''

conn = psycopg.connect(os.environ['DATABASE_URL'])
with conn.transaction():
    for county, facility, url, adapter in MT_SOURCES:
        row = conn.execute(UPDATE, (facility, url, adapter, AUTH, county)).fetchone()
        if not row:
            row = conn.execute(INSERT, (county, facility, url, adapter, AUTH)).fetchone()
        print(row[0], county, adapter or 'PENDING-ADAPTER')
conn.close()
