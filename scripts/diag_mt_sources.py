import os, psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row)

rows = conn.execute("""
    SELECT j.id, j.state, j.county, j.facility_name, j.adapter, j.source_url, j.enabled, j.staging_only, j.review_status
    FROM records.jurisdictions j
    WHERE j.state = 'MT'
    ORDER BY j.adapter, j.county
""").fetchall()

for r in rows:
    status = 'ON' if r['enabled'] else ('STAGE' if r['staging_only'] else 'off')
    print(f"{r['adapter']:<28} {status:<5} {r['county']:<18} {r['source_url'][:90]}")
