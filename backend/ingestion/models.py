from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any


def _clean(value: str | None) -> str | None:
    return " ".join(value.split()) if value and value.strip() else None


def _aware(value: datetime | None, field_name: str) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


@dataclass(frozen=True, slots=True)
class Charge:
    charge_description: str
    statute: str | None = None
    degree: str | None = None
    bond_amount: Decimal | None = None
    court_date: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "charge_description", _clean(self.charge_description) or "Unknown charge")
        object.__setattr__(self, "statute", _clean(self.statute))
        object.__setattr__(self, "degree", _clean(self.degree))
        _aware(self.court_date, "court_date")
        if self.bond_amount is not None and self.bond_amount < 0:
            raise ValueError("bond_amount cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "charge_description": self.charge_description,
            "statute": self.statute,
            "degree": self.degree,
            "bond_amount": str(self.bond_amount) if self.bond_amount is not None else None,
            "court_date": self.court_date.isoformat() if self.court_date else None,
        }


@dataclass(frozen=True, slots=True)
class BookingRecord:
    facility_id: str
    booking_number: str
    first_name: str
    last_name: str
    middle_name: str | None = None
    date_of_birth: date | None = None
    age: int | None = None
    booking_date: datetime | None = None
    release_date: datetime | None = None
    charges: tuple[Charge, ...] = ()
    total_bond_amount: Decimal | None = None
    mugshot_url: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        for name in ("facility_id", "booking_number", "first_name", "last_name"):
            value = _clean(getattr(self, name))
            if not value:
                raise ValueError(f"{name} is required")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "middle_name", _clean(self.middle_name))
        object.__setattr__(self, "mugshot_url", _clean(self.mugshot_url))
        _aware(self.booking_date, "booking_date")
        _aware(self.release_date, "release_date")
        _aware(self.scraped_at, "scraped_at")
        if self.age is not None and not 0 <= self.age <= 125:
            raise ValueError("age must be between 0 and 125")
        if self.total_bond_amount is not None and self.total_bond_amount < 0:
            raise ValueError("total_bond_amount cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "facility_id": self.facility_id,
            "booking_number": self.booking_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "charges": [charge.to_dict() for charge in self.charges],
            "total_bond_amount": str(self.total_bond_amount) if self.total_bond_amount is not None else None,
            "mugshot_url": self.mugshot_url,
            "raw_data": self.raw_data,
            "scraped_at": self.scraped_at.isoformat(),
        }


BOOKING_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "JailMap staged booking",
    "type": "object",
    "required": ["facility_id", "booking_number", "first_name", "last_name", "charges", "raw_data", "scraped_at"],
    "properties": {
        "facility_id": {"type": "string", "minLength": 1},
        "booking_number": {"type": "string", "minLength": 1},
        "first_name": {"type": "string", "minLength": 1},
        "last_name": {"type": "string", "minLength": 1},
        "middle_name": {"type": ["string", "null"]},
        "date_of_birth": {"type": ["string", "null"], "format": "date"},
        "age": {"type": ["integer", "null"], "minimum": 0, "maximum": 125},
        "booking_date": {"type": ["string", "null"], "format": "date-time"},
        "release_date": {"type": ["string", "null"], "format": "date-time"},
        "charges": {"type": "array", "items": {"type": "object"}},
        "total_bond_amount": {"type": ["string", "null"], "pattern": "^[0-9]+(?:\\.[0-9]+)?$"},
        "mugshot_url": {"type": ["string", "null"]},
        "raw_data": {"type": "object"},
        "scraped_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}
