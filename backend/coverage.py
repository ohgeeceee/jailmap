"""Database-backed state/county ingestion inventory; never reads account SQLite."""
import argparse
import json
from backend.db import pool
from backend.national_seed import STATES

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', type=str.upper, choices=sorted(STATES))
    parser.add_argument('--county-fips', help='List facility candidates and source work for a five-digit county FIPS')
    args = parser.parse_args()
    with pool, pool.connection() as connection:
        if args.county_fips:
            if len(args.county_fips)!=5 or not args.county_fips.isdigit(): parser.error('County FIPS must be five digits')
            rows = connection.execute('''SELECT j.id,j.name,j."isActive" AS public_directory,
                q.status,q.source_url,q.adapter,q.notes,f.source_vintage
                FROM public."Jail" j JOIN public."County" c ON c.id=j."countyId"
                LEFT JOIN records.facility_ingestion_queue q ON q.jail_id=j.id
                LEFT JOIN records.facility_sources f ON f.jail_id=j.id
                WHERE c."fipsCode"=%s ORDER BY j.name''',(args.county_fips,)).fetchall()
        elif args.state:
            rows = connection.execute('''SELECT s.abbrev,c.name,c."fipsCode",q.status,q.source_url,q.adapter,q.notes
                FROM records.county_ingestion_queue q JOIN public."County" c ON c.id=q.county_id
                JOIN public."State" s ON s.id=c."stateId" WHERE s.abbrev=%s ORDER BY c.name''', (args.state,)).fetchall()
        else:
            rows = connection.execute('SELECT * FROM records.state_ingestion_status ORDER BY abbrev').fetchall()
        print(json.dumps(rows,indent=2,default=str))

if __name__ == '__main__':
    main()
