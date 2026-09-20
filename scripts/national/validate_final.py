#!/usr/bin/env python3
"""Validate leads-final.csv has proper 2-letter state codes throughout."""
import csv

bad = 0
good = 0
with open("data/national/leads-final.csv", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=2):
        state = row.get("state", "").strip()
        url = row.get("source_url", "").strip()
        ev = row.get("evidence_url", "").strip()
        if len(state) != 2 or not state.isalpha() or not state.isupper():
            bad += 1
            if bad <= 10:
                print(f"Line {i}: state={state!r} county={row.get('county')!r} url={url!r}")
        else:
            good += 1
        # Also check URLs
        if not url.startswith("https://"):
            print(f"Line {i}: BAD URL: {url!r}")
        if not ev.startswith("https://"):
            print(f"Line {i}: BAD EVIDENCE URL: {ev!r}")

print(f"\ngood: {good}, bad state: {bad}")
