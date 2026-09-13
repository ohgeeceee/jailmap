"""Carry forward existing ID/SD research as unverified leads, never enabled sources."""
import csv
from pathlib import Path
from urllib.parse import urlsplit
from backend.db import pool

def key(value):
    return value.strip().lower().replace('-',' ').removesuffix(' county')

def main():
    imported=0;unmatched=0;no_https=0
    with pool,pool.connection() as connection,connection.transaction():
        counties=connection.execute('''SELECT c.id,c.name,s.abbrev FROM public."County" c
            JOIN public."State" s ON s.id=c."stateId" WHERE s.abbrev IN ('ID','SD')''').fetchall()
        lookup={(r['abbrev'],key(r['name'])):r['id'] for r in counties}
        for name in ('idaho-jail-sources.csv','sd-jail-sources.csv'):
            with (Path(__file__).parent/'discovery'/name).open(encoding='utf-8-sig',newline='') as source:
                for row in csv.DictReader(source):
                    county=lookup.get((row['state'],key(row['county'])))
                    if not county:
                        unmatched+=1;continue
                    url=(row.get('source_url') or '').strip()
                    parsed=urlsplit(url)
                    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
                        no_https+=1;continue
                    note='Legacy discovery lead; endpoint and access status not verified in this run. '+(row.get('notes') or '')
                    updated=connection.execute('''UPDATE records.county_ingestion_queue SET source_url=%s,
                        notes=%s,updated_at=now() WHERE county_id=%s AND source_url IS NULL RETURNING county_id''',
                        (url,note[:3000],county)).fetchone()
                    imported+=int(updated is not None)
    print(f'Imported {imported} unverified discovery leads; {unmatched} unmatched counties; {no_https} without an acceptable HTTPS URL')

if __name__=='__main__': main()
