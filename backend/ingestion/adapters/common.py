from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any
from zoneinfo import ZoneInfo

from ..models import BookingRecord, Charge


def value_at(item: dict[str, Any], path: str | None, default: Any = None) -> Any:
    current: Any = item
    for key in (path or "").split("."):
        if not key:
            return default
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def parse_datetime(value: Any, timezone_name: str) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    return parsed.replace(tzinfo=ZoneInfo(timezone_name)) if parsed.tzinfo is None else parsed


def parse_date(value: Any) -> date | None:
    return date.fromisoformat(str(value).strip()) if value else None


def decimal_value(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if text.casefold() in {"no bond", "none", "n/a", "not available", "sentenced"}:
        return None
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text):
        return None
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid monetary value: {value!r}") from exc


def split_name(value: Any) -> tuple[str, str | None, str]:
    text = " ".join(str(value or "").split())
    if "," in text:
        last, rest = [part.strip() for part in text.split(",", 1)]
        parts = rest.split()
        return (parts[0] if parts else "Unknown", " ".join(parts[1:]) or None, last or "Unknown")
    parts = text.split()
    return (parts[0] if parts else "Unknown", " ".join(parts[1:-1]) or None, parts[-1] if len(parts) > 1 else "Unknown")


def normalize_mapping(item: dict[str, Any], facility_id: str, timezone_name: str, field_map: dict[str, str]) -> BookingRecord:
    def get(name: str, default: Any = None) -> Any:
        return value_at(item, field_map.get(name), default)

    first, middle, last = get("first_name"), get("middle_name"), get("last_name")
    if not first or not last:
        first, middle, last = split_name(get("name"))
    raw_charges = get("charges", [])
    if isinstance(raw_charges, str):
        raw_charges = [{"charge_description": raw_charges}]
    charges = tuple(
        Charge(
            charge_description=str(value_at(raw, field_map.get("charge_description", "charge_description"), "Unknown charge")),
            statute=value_at(raw, field_map.get("statute", "statute")),
            degree=value_at(raw, field_map.get("degree", "degree")),
            bond_amount=decimal_value(value_at(raw, field_map.get("bond_amount", "bond_amount"))),
            court_date=parse_datetime(value_at(raw, field_map.get("court_date", "court_date")), timezone_name),
        )
        for raw in raw_charges
        if isinstance(raw, dict)
    )
    return BookingRecord(
        facility_id=facility_id,
        booking_number=str(get("booking_number", "")),
        first_name=str(first or ""),
        middle_name=str(middle) if middle else None,
        last_name=str(last or ""),
        date_of_birth=parse_date(get("date_of_birth")),
        age=int(get("age")) if get("age") not in (None, "") else None,
        booking_date=parse_datetime(get("booking_date"), timezone_name),
        release_date=parse_datetime(get("release_date"), timezone_name),
        charges=charges,
        total_bond_amount=decimal_value(get("total_bond_amount")),
        mugshot_url=get("mugshot_url"),
        raw_data=item,
    )
