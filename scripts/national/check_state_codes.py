#!/usr/bin/env python3
"""Check leads-final.csv for rows with bad state codes."""
import csv

with open("data/national/leads-final.csv", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=2):
        state = row.get("state", "").strip()
        if len(state) != 2 or not state.isupper():
            print(f"Line {i}: state={state!r} county={row.get('county')!r} url={row.get('source_url')!r}")
