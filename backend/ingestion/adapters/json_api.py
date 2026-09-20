from __future__ import annotations

from typing import Any, Iterable

from ..base import BaseAdapter
from ..models import BookingRecord
from .common import normalize_mapping, value_at


class JsonApiAdapter(BaseAdapter):
    def fetch(self) -> list[dict[str, Any]]:
        options = self.config.options
        page_param = options.get("page_param", "page")
        start_page = int(options.get("start_page", 1))
        max_pages = min(int(options.get("max_pages", 100)), 500)
        max_records = min(int(options.get("max_records", 10_000)), 50_000)
        records: list[dict[str, Any]] = []
        for page in range(start_page, start_page + max_pages):
            params = {**options.get("params", {}), page_param: page}
            response = self.client.get(self.config.source_url, params=params)
            response.raise_for_status()
            payload = response.json()
            items = value_at(payload, options.get("items_path", "results"), [])
            if not isinstance(items, list):
                raise ValueError("items_path did not resolve to a JSON array")
            records.extend(item for item in items if isinstance(item, dict))
            if not items or len(records) >= max_records:
                break
            next_path = options.get("next_path")
            if next_path and not value_at(payload, next_path):
                break
        return records[:max_records]

    def parse(self, artifact: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        return artifact

    def normalize(self, item: dict[str, Any]) -> BookingRecord:
        return normalize_mapping(item, self.config.facility_id, self.config.timezone, self.config.options.get("field_map", {}))
