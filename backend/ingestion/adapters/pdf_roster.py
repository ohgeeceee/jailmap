from __future__ import annotations

import io
import re
from typing import Any, Iterable

import pdfplumber

from ..base import BaseAdapter
from ..models import BookingRecord
from .common import normalize_mapping


class PdfRosterAdapter(BaseAdapter):
    """Parses text-based PDFs with a source-specific named-group row pattern."""

    def fetch(self) -> bytes:
        response = self.client.get(self.config.source_url)
        response.raise_for_status()
        return response.content

    def parse(self, artifact: bytes) -> Iterable[dict[str, Any]]:
        pattern_text = self.config.options.get("row_pattern")
        if not pattern_text:
            raise ValueError("PDF driver requires options.row_pattern with named capture groups")
        pattern = re.compile(pattern_text)
        rows: list[dict[str, Any]] = []
        with pdfplumber.open(io.BytesIO(artifact)) as document:
            for page in document.pages[: int(self.config.options.get("max_pages", 200))]:
                for match in pattern.finditer(page.extract_text() or ""):
                    rows.append(match.groupdict())
        return rows

    def normalize(self, item: dict[str, Any]) -> BookingRecord:
        return normalize_mapping(item, self.config.facility_id, self.config.timezone, self.config.options.get("field_map", {}))
