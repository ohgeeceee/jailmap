#!/usr/bin/env python3
"""Register reviewed staging-only scraper jurisdictions.

This script creates or updates scraper rows in records.jurisdictions without
enabling public publication. It is intentionally narrow: each entry names an
official source URL, a concrete adapter, and an authorization reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.db import pool


@dataclass(frozen=True)
class StagingScraper:
    state: str
    county: str
    facility_name: str
    source_url: str
    adapter: str
    authorization_reference: str


SCRAPERS = [
    StagingScraper(
        state="ID",
        county="Bonneville",
        facility_name="Bonneville County Jail",
        source_url="https://bonnevillesheriff.com/bonneville-county-jail/inmate-list/",
        adapter="bonneville_html_staging",
        authorization_reference="Official Bonneville County Sheriff's Office inmate list page; staging-only review 2026-09-13.",
    ),
    StagingScraper(
        state="ID",
        county="Franklin",
        facility_name="Franklin County Jail",
        source_url="https://www.franklinsheriff.org/roster.php",
        adapter="franklin_html_staging",
        authorization_reference="Official Franklin County Sheriff's Office roster page; staging-only review 2026-09-13.",
    ),
    StagingScraper(
        state="ID",
        county="Power",
        facility_name="Power County Jail",
        source_url="https://jail.powercounty.gov/jailroster/",
        adapter="power_html_staging",
        authorization_reference="Official Power County jail roster page; staging-only review 2026-09-13.",
    ),
]


def main() -> None:
    registered = 0
    with pool, pool.connection() as connection, connection.transaction():
        for source in SCRAPERS:
            connection.execute(
                """
                INSERT INTO records.jurisdictions (
                    state, county, facility_name, source_url, adapter,
                    authorization_reference, enabled, review_status,
                    staging_only
                )
                VALUES (%s, %s, %s, %s, %s, %s, false, 'verified', true)
                ON CONFLICT (state, county, facility_name) DO UPDATE SET
                    source_url = EXCLUDED.source_url,
                    adapter = EXCLUDED.adapter,
                    authorization_reference = EXCLUDED.authorization_reference,
                    enabled = false,
                    review_status = 'verified',
                    staging_only = true
                """,
                (
                    source.state,
                    source.county,
                    source.facility_name,
                    source.source_url,
                    source.adapter,
                    source.authorization_reference,
                ),
            )
            connection.execute(
                """
                UPDATE records.county_ingestion_queue q
                   SET status = 'testing',
                       source_url = %s,
                       adapter = %s,
                       notes = %s,
                       updated_at = now()
                  FROM public."County" c
                  JOIN public."State" s ON s.id = c."stateId"
                 WHERE q.county_id = c.id
                   AND s.abbrev = %s
                   AND c.name = %s
                """,
                (
                    source.source_url,
                    source.adapter,
                    source.authorization_reference,
                    source.state,
                    source.county + " County",
                ),
            )
            registered += 1
    print(f"Registered {registered} staging-only scraper sources.")


if __name__ == "__main__":
    main()
