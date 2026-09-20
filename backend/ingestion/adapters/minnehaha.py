from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from ..base import BaseAdapter
from ..models import BookingRecord, Charge
from .common import decimal_value


class MinnehahaRosterAdapter(BaseAdapter):
    """Explicit parser for the county's nine-column body/seven-header roster."""

    def fetch(self) -> str:
        response = self.client.get(self.config.source_url)
        response.raise_for_status()
        return response.text

    def parse(self, artifact: str) -> Iterable[dict[str, Any]]:
        soup = BeautifulSoup(artifact, "html.parser")
        rows = []
        for row in soup.select("table.tablesorter tbody tr"):
            cells = row.select("td")
            if len(cells) != 9:
                continue
            facility = cells[6].get_text(" ", strip=True)
            if facility != "Jail":
                continue
            last_name = cells[2].get_text(" ", strip=True)
            booking_match = re.search(r"(\d{4,})", cells[3].get_text(" ", strip=True))
            if not booking_match:
                continue
            rows.append({
                "first_name": cells[0].get_text(" ", strip=True),
                "middle_name": cells[1].get_text(" ", strip=True),
                "last_name": last_name,
                "booking_number": booking_match.group(1),
                "booking_date": cells[4].get_text(" ", strip=True),
                "booking_time": cells[5].get_text(" ", strip=True),
                "facility": facility,
                "bond": cells[7].get_text(" ", strip=True),
                "charge": cells[8].get_text(" | ", strip=True),
            })
        return rows

    def normalize(self, item: dict[str, Any]) -> BookingRecord:
        local_zone = ZoneInfo(self.config.timezone)
        value = f"{item['booking_date']} {item['booking_time']}".strip()
        booking_date = None
        for pattern in (
            "%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p",
            "%m/%d/%Y %I:%M %p", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M",
        ):
            try:
                booking_date = datetime.strptime(value, pattern).replace(tzinfo=local_zone)
                break
            except ValueError:
                continue
        if booking_date is None:
            raise ValueError("Minnehaha row has an unrecognized booking timestamp")
        charge_text = " ".join(item["charge"].split())
        charges = (Charge(charge_description=charge_text),) if charge_text else ()
        bond: Decimal | None = decimal_value(item["bond"])
        return BookingRecord(
            facility_id=self.config.facility_id,
            booking_number=item["booking_number"],
            first_name=item["first_name"],
            middle_name=item["middle_name"] or None,
            last_name=item["last_name"],
            booking_date=booking_date,
            charges=charges,
            total_bond_amount=bond,
            raw_data=item,
        )
