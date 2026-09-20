from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import httpx

from .http import ResilientHttpClient
from .models import BookingRecord


@dataclass(frozen=True, slots=True)
class AdapterConfig:
    facility_id: str
    source_url: str
    state: str | None = None
    county: str | None = None
    vendor: str | None = None
    timezone: str = "UTC"
    options: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """All source adapters follow fetch -> parse -> normalize -> export."""

    def __init__(self, config: AdapterConfig, client: httpx.Client | None = None) -> None:
        self.config = config
        self.client = client or ResilientHttpClient(
            min_interval_seconds=float(config.options.get("min_interval_seconds", 1.0)),
            max_attempts=int(config.options.get("max_attempts", 4)),
        )
        self._owns_client = client is None

    @abstractmethod
    def fetch(self) -> Any: ...

    @abstractmethod
    def parse(self, artifact: Any) -> Iterable[dict[str, Any]]: ...

    @abstractmethod
    def normalize(self, item: dict[str, Any]) -> BookingRecord: ...

    def run(self) -> list[BookingRecord]:
        try:
            return [self.normalize(item) for item in self.parse(self.fetch())]
        finally:
            if self._owns_client:
                self.client.close()

    def export(self, records: Iterable[BookingRecord], destination: str | Path | None = None) -> str:
        output = json.dumps([record.to_dict() for record in records], indent=2, ensure_ascii=False)
        if destination:
            Path(destination).write_text(output + "\n", encoding="utf-8")
        return output
