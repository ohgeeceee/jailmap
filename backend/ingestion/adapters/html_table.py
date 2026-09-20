from __future__ import annotations

from typing import Any, Iterable

from bs4 import BeautifulSoup

from ..base import BaseAdapter
from ..models import BookingRecord
from .common import normalize_mapping


DEFAULT_HEADERS = {
    "booking #": "booking_number", "booking number": "booking_number", "name": "name",
    "first name": "first_name", "middle name": "middle_name", "last name": "last_name",
    "booked": "booking_date", "booking date": "booking_date", "release date": "release_date",
    "dob": "date_of_birth", "age": "age", "charge": "charges", "bond": "total_bond_amount",
}


class HtmlTableAdapter(BaseAdapter):
    def fetch(self) -> str:
        response = self.client.get(self.config.source_url)
        response.raise_for_status()
        return response.text

    def parse(self, artifact: str) -> Iterable[dict[str, Any]]:
        soup = BeautifulSoup(artifact, "html.parser")
        table = soup.select_one(self.config.options.get("table_selector", "table"))
        if table is None:
            raise ValueError("configured roster table was not found")
        rows = table.select("tr")
        if not rows:
            return []
        labels = [cell.get_text(" ", strip=True).lower() for cell in rows[0].select("th,td")]
        header_map = {**DEFAULT_HEADERS, **self.config.options.get("header_map", {})}
        keys = [header_map.get(label, label.replace(" ", "_")) for label in labels]
        parsed = []
        for row in rows[1:]:
            values = [cell.get_text(" ", strip=True) for cell in row.select("td")]
            if not values:
                continue
            item = dict(zip(keys, values, strict=False))
            row_filters = self.config.options.get("row_filters", {})
            if any(str(item.get(key, "")) not in {str(value) for value in allowed} for key, allowed in row_filters.items()):
                continue
            if isinstance(item.get("charges"), str):
                item["charges"] = [{"charge_description": item["charges"]}]
            parsed.append(item)
        return parsed

    def normalize(self, item: dict[str, Any]) -> BookingRecord:
        field_map = {key: key for key in item}
        field_map.update(self.config.options.get("field_map", {}))
        return normalize_mapping(item, self.config.facility_id, self.config.timezone, field_map)
