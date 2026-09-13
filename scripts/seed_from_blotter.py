#!/usr/bin/env python3
"""Seed JailMap's PostgreSQL from Montana Blotter's SQLite jail_bookings."""
import sqlite3
import re
from datetime import datetime, timedelta, timezone
import sys

print("Loading...")

# Connect to SQLite (Blotter)
sl_conn = sqlite3.connect('/tmp/blotter.db')
sl_conn.row_factory = sqlite3.Row

# Get recent bookings (last 48h)
cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
rows = sl_conn.execute("""
    SELECT id, person_name, county_slug, county_name, facility_name,
           age, booking_number, booking_at, charges_summary, source_url
    FROM jail_bookings
    WHERE booking_at >= ?
    ORDER BY booking_at DESC
""", (cutoff,)).fetchall()

print(f"Found {len(rows)} bookings in last 48h from Blotter")

# Connect to PostgreSQL (JailMap)
from backend.db import pool
pool.open()

# Build county-slug → jurisdiction-id map
with pool.connection() as conn:
    jurisdictions = conn.execute(
        "SELECT id, county, state FROM records.jurisdictions WHERE state='MT'"
    ).fetchall()

jurisdiction_map = {}
for j in jurisdictions:
    slug = j['county'].lower().replace(' ', '-').replace('and', 'and')
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    jurisdiction_map[slug] = str(j['id'])
    jurisdiction_map[j['county'].lower()] = str(j['id'])

print(f"Jurisdiction map has {len(jurisdiction_map)} entries")

def split_name(full_name):
    """Split 'Last, First' or 'First Last' into (first, last)."""
    full_name = (full_name or 'Unknown').strip()
    if ',' in full_name:
        parts = [p.strip() for p in full_name.split(',', 1)]
        return parts[1] if len(parts) > 1 else parts[0], parts[0]
    parts = full_name.split()
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    return parts[0], ''

def make_booking_number(row):
    if row['booking_number']:
        return row['booking_number'][:50]
    return f"BLOTTER-{row['id']}"

inserted = 0
skipped = 0
no_juris = 0
duplicates = 0

with pool.connection() as conn:
    for row in rows:
        county_slug = row['county_slug']
        juris_id = jurisdiction_map.get(county_slug)
        if not juris_id:
            juris_id = jurisdiction_map.get(county_slug.replace('-', ' '))
        if not juris_id:
            no_juris += 1
            continue

        first_name, last_name = split_name(row['person_name'])
        booking_num = make_booking_number(row)

        booking_at = row['booking_at'] or datetime.now(timezone.utc).isoformat()
        if isinstance(booking_at, str):
            try:
                datetime.fromisoformat(booking_at.replace(' ', 'T'))
            except:
                booking_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        existing = conn.execute(
            "SELECT id FROM records.inmates WHERE jurisdiction_id=%s AND booking_number=%s",
            (juris_id, booking_num)
        ).fetchone()
        if existing:
            duplicates += 1
            continue

        conn.execute("""
            INSERT INTO records.inmates
                (jurisdiction_id, booking_number, first_name, last_name,
                 booking_date, source_updated_at, visibility, observed_at)
            VALUES (%s, %s, %s, %s, %s, now(), 'public', now())
        """, (juris_id, booking_num, first_name, last_name, booking_at))

        new_id = conn.execute(
            "SELECT id FROM records.inmates WHERE jurisdiction_id=%s AND booking_number=%s",
            (juris_id, booking_num)
        ).fetchone()

        if new_id and row['charges_summary']:
            charges = [c.strip() for c in row['charges_summary'].split(';') if c.strip()]
            for i, charge_desc in enumerate(charges[:10]):
                source_id = f"charge-{i}"
                existing_charge = conn.execute(
                    "SELECT id FROM records.charges WHERE inmate_id=%s AND source_id=%s",
                    (new_id['id'], source_id)
                ).fetchone()
                if not existing_charge:
                    conn.execute("""
                        INSERT INTO records.charges (inmate_id, source_id, description)
                        VALUES (%s, %s, %s)
                    """, (new_id['id'], source_id, charge_desc[:500]))

        inserted += 1

    conn.commit()

sl_conn.close()
pool.close()

print(f"Inserted: {inserted}")
print(f"Duplicates skipped: {duplicates}")
print(f"No jurisdiction match: {no_juris}")
