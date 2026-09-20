#!/usr/bin/env python3
"""Combine all lead sources into one unified CSV."""
import csv
from pathlib import Path

FIELDS = [
    "state", "county", "facility", "source_url", "source_owner",
    "source_kind", "access_status", "adapter_strategy",
    "publication_default", "evidence_url", "notes",
]

sources = [
    Path("data/national/official-jail-source-leads.csv"),      # 674 rows
    Path("data/national/official-jail-source-leads-new.csv"),   # 673 rows
    Path("data/national/leads-census.csv"),                     # 133 rows
]

seen = set()
rows = []
added = 0

for path in sources:
    if not path.exists():
        print(f"SKIP (missing): {path}")
        continue
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        src_count = 0
        for row in reader:
            key = (row.get("state", "").strip().upper(),
                   row.get("county", "").strip().lower(),
                   row.get("source_url", "").strip())
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
            src_count += 1
            added += 1
    print(f"{path.name}: {src_count} added")

# Write to a temp file first
out_path = Path("data/national/leads-combined.csv")
with out_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTotal unique leads: {added}")
print(f"Written to: {out_path}")
