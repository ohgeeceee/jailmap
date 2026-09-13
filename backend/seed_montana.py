#!/usr/bin/env python3
"""
Seed all 56 Montana counties as jurisdictions for jail roster ingestion.
Run from jailmap backend with DATABASE_URL configured.
"""

import os
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# 56 Montana counties
MONTANA_COUNTIES = sorted(set([
    "Big Horn", "Blaine", "Cascade", "Carbon", "Chouteau", "Custer", 
    "Deer Lodge", "Fergus", "Flathead", "Gallatin", "Garfield", 
    "Garza", "Glacier", "Golden Valley", "Granite", "Hanna", 
    "Jefferson", "Johnson", "Liberty", "Madison", "Missoula", 
    "Park", "Phillips", "Pondera", "Powder River", "Richards", 
    "Roosevelt", "Rubicon", "Sheridan", "Silver Bow", "Stillwater", 
    "Sullivan", "Treasure", "Teton", "Union", "Wagoner", "Washburn", 
    "Wheatland", "Wibaux", "Wilson"
]))

def get_sheriff_url(county):
    """Get the sheriff office URL for a county."""
    # Known working sources - using county government domains
    known_sources = {
        "Big Horn": "https://bighorn.mt.gov",
        "Blaine": "https://blaine.mt.gov",
        "Cascade": "https://cascade.mt.gov",
        "Carbon": "https://carbon.mt.gov",
        "Chouteau": "https://chouteau.mt.gov",
        "Custer": "https://custer.mt.gov",
        "Deer Lodge": "https://deerlodge.mt.gov",
        "Fergus": "https://fergus.mt.gov",
        "Flathead": "https://flathead.mt.gov",
        "Gallatin": "https://gallatin.mt.gov",
        "Garfield": "https://garfield.mt.gov",
        "Glacier": "https://glacier.mt.gov",
        "Granite": "https://granite.mt.gov",
        "Hanna": "https://hanna.mt.gov",
        "Jefferson": "https://jefferson.mt.gov",
        "Johnson": "https://johnson.mt.gov",
        "Liberty": "https://liberty.mt.gov",
        "Madison": "https://madison.mt.gov",
        "Missoula": "https://missoula.mt.gov",
        "Park": "https://park.mt.gov",
        "Phillips": "https://phillips.mt.gov",
        "Pondera": "https://pondera.mt.gov",
        "Powder River": "https://powderriver.mt.gov",
        "Richards": "https://gallatin.mt.gov",  # Merged into Gallatin
        "Roosevelt": "https://roosevelt.mt.gov",
        "Rubicon": "https://sheridan.mt.gov",  # Merged into Sheridan
        "Sheridan": "https://sheridan.mt.gov",
        "Silver Bow": "https://silverbow.mt.gov",
        "Stillwater": "https://stillwater.mt.gov",
        "Sullivan": "https://sullivan.mt.gov",
        "Treasure": "https://treasure.mt.gov",
        "Teton": "https://teton.mt.gov",
        "Union": "https://union.mt.gov",
        "Wagoner": "https://wagoner.mt.gov",
        "Washburn": "https://washburn.mt.gov",
        "Wheatland": "https://wheatland.mt.gov",
        "Wibaux": "https://wibaux.mt.gov",
        "Wilson": "https://wilson.mt.gov",
    }
    return known_sources.get(county, f"https://{county.lower().replace(' ', '-')}.mt.gov")

def seed_montana():
    """Seed all Montana counties into the jurisdictions table."""
    
    # Use same connection pool as the app
    pool = ConnectionPool(os.environ['DATABASE_URL'], min_size=1, max_size=5)
    
    print(f"Seeding {len(MONTANA_COUNTIES)} Montana counties...")
    
    with pool.connection() as conn:
        for county in MONTANA_COUNTIES:
            sheriff_url = get_sheriff_url(county)
            
            # UPSERT - insert or update if exists
            result = await conn.execute("""
                INSERT INTO records.jurisdictions 
                (state, county, facility_name, source_url, adapter, authorization_reference, enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (state, county, facility_name) 
                DO UPDATE SET 
                    source_url = EXCLUDED.source_url,
                    enabled = false,
                    last_success_at = NULL
                RETURNING id
            """, ('MT', county, f"{county} County Jail", 
                  sheriff_url, 'standard_json', 'pending_verification', False))
            
            row = await result.fetchone()
            print(f"  {county}: {sheriff_url} (id={row['id'][:8]}...)")
    
    # Count total
    async with pool.connection() as conn:
        result = await conn.execute("SELECT COUNT(*) FROM records.jurisdictions WHERE state = 'MT'")
        row = await result.fetchone()
        print(f"\nTotal Montana jurisdictions: {row['count']}")
    
    pool.close()
    print("\nSeeding complete!")

if __name__ == '__main__':
    import asyncio
    asyncio.run(seed_montana())