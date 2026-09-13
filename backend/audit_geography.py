"""Read-only national directory audit. No person records are accessed."""
import json
from backend.db import pool
from backend.national_seed import STATES


def main():
    with pool, pool.connection() as connection:
        states = connection.execute('SELECT abbrev FROM public."State" ORDER BY abbrev').fetchall()
        present = {row['abbrev'] for row in states}
        checks = {
            'missing_states': sorted(set(STATES) - present),
            'unexpected_states': sorted(present - set(STATES)),
        }
        queries = {
            'counties_without_queue': '''SELECT count(*) AS n FROM public."County" c
                LEFT JOIN records.county_ingestion_queue q ON q.county_id=c.id WHERE q.county_id IS NULL''',
            'facilities_without_queue': '''SELECT count(*) AS n FROM public."Jail" j
                LEFT JOIN records.facility_ingestion_queue q ON q.jail_id=j.id WHERE q.jail_id IS NULL''',
            'facility_geography_mismatches': '''SELECT count(*) AS n FROM public."Jail" j
                JOIN public."County" c ON c.id=j."countyId" WHERE j."stateId"<>c."stateId"''',
            'duplicate_county_fips': '''SELECT count(*) AS n FROM
                (SELECT "fipsCode" FROM public."County" GROUP BY "fipsCode" HAVING count(*)>1) d''',
        }
        for name, query in queries.items():
            checks[name] = connection.execute(query).fetchone()['n']
        totals = connection.execute('''SELECT
            (SELECT count(*) FROM public."State") AS states,
            (SELECT count(*) FROM public."County") AS counties,
            (SELECT count(*) FROM public."Jail") AS facilities''').fetchone()
        passed = not any(checks.values())
        print(json.dumps({'passed': passed, 'totals': totals, 'checks': checks}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
