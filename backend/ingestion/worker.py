from __future__ import annotations

import json
from collections.abc import Iterable

from .models import BookingRecord


def booking_upsert_sql() -> str:
    return """
        INSERT INTO records.adapter_bookings_staging (
            facility_id, booking_number, first_name, last_name, middle_name,
            date_of_birth, age, booking_date, release_date, charges,
            total_bond_amount, mugshot_url, raw_data, scraped_at
        ) VALUES (
            %(facility_id)s, %(booking_number)s, %(first_name)s, %(last_name)s, %(middle_name)s,
            %(date_of_birth)s, %(age)s, %(booking_date)s, %(release_date)s, %(charges)s::jsonb,
            %(total_bond_amount)s, %(mugshot_url)s, %(raw_data)s::jsonb, %(scraped_at)s
        )
        ON CONFLICT (facility_id, booking_number) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            middle_name = EXCLUDED.middle_name,
            date_of_birth = EXCLUDED.date_of_birth,
            age = EXCLUDED.age,
            booking_date = EXCLUDED.booking_date,
            release_date = EXCLUDED.release_date,
            charges = EXCLUDED.charges,
            total_bond_amount = EXCLUDED.total_bond_amount,
            mugshot_url = EXCLUDED.mugshot_url,
            raw_data = EXCLUDED.raw_data,
            scraped_at = EXCLUDED.scraped_at,
            updated_at = now()
        WHERE EXCLUDED.scraped_at >= records.adapter_bookings_staging.scraped_at
    """


def _params(record: BookingRecord) -> dict:
    payload = record.to_dict()
    payload["charges"] = json.dumps(payload["charges"])
    payload["raw_data"] = json.dumps(payload["raw_data"])
    return payload


def ingest_records(connection, records: Iterable[BookingRecord]) -> int:
    """Atomically upsert validated records; caller owns connection lifecycle."""
    count = 0
    with connection.transaction():
        with connection.cursor() as cursor:
            for record in records:
                cursor.execute(booking_upsert_sql(), _params(record))
                count += 1
    return count


def log_failure(connection, *, facility_id: str | None, driver: str, stage: str, error: Exception) -> None:
    """Store diagnostic metadata only; never store response bodies or record PII."""
    safe_message = f"{stage} failed; inspect restricted worker logs using the run correlation ID"
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO records.adapter_failures
                   (facility_id, adapter_driver, failure_stage, error_type, safe_message)
                   VALUES (%s, %s, %s, %s, %s)""",
                (facility_id, driver, stage, type(error).__name__, safe_message),
            )
