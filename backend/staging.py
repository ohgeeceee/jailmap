"""Helpers for private staging snapshots from reviewed source adapters."""
from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from uuid import UUID


def json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def compact(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def missing(value):
    if value is None:
        return True
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return not compact(value)


def staging_key(row, index):
    for field in ("booking_number", "inmate_id", "jms_number", "cid", "source_id"):
        value = compact(row.get(field))
        if value:
            return value[:200]
    basis = "|".join(compact(row.get(field)) for field in (
        "full_name", "first_name", "last_name", "booking_date", "source_url", "notes"))
    if not basis.strip("|"):
        basis = f"row-{index}"
    return "staging-" + sha256(basis.encode("utf-8")).hexdigest()[:32]


def staging_snapshot_at(row):
    for field in ("source_updated_at", "pulled_at", "booking_date"):
        value = row.get(field)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
    return datetime.now(timezone.utc)


def prepare_staging_rows(rows):
    prepared = []
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError("Staging adapter returned a non-object row")
        key = staging_key(row, index)
        if key in seen:
            raise ValueError("Duplicate staging keys in source snapshot")
        seen.add(key)
        payload = dict(row)
        payload.setdefault("quality_flags", [])
        flags = payload["quality_flags"]
        if not isinstance(flags, list):
            raise ValueError("Invalid quality_flags")
        if missing(payload.get("booking_number")):
            flags.append("missing_booking_number")
        if missing(payload.get("booking_date")):
            flags.append("missing_booking_date")
        if missing(payload.get("charges")):
            flags.append("charges_not_provided")
        if missing(payload.get("bonds")):
            flags.append("bonds_not_provided")
        payload["staging_key"] = key
        prepared.append((key, payload, staging_snapshot_at(payload)))
    return prepared
