#!/usr/bin/env python3
"""Merge existing + new leads, dedupe, write final CSV."""
import csv
from pathlib import Path

FIELDS = [
    "state", "county", "facility", "source_url", "source_owner",
    "source_kind", "access_status", "adapter_strategy",
    "publication_default", "evidence_url", "notes",
]

existing = Path("data/national/official-jail-source-leads.csv")
new = Path("data/national/official-jail-source-leads-new.csv")
merged = Path("data/national/official-jail-source-leads.csv")

seen = set()
rows = []

def key(row):
    return (row["state"], row["county"].strip().lower(), row["source_url"])

for path in [existing, new]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            k = key(row)
            if k in seen:
                continue
            seen.add(k)
            rows.append(row)

with merged.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

print(f"Merged: {len(rows)} unique leads ({len(seen)} keys)")
print(f"  from existing: {existing}")
print(f"  + new: {new}")
print(f"  -> {merged}")
