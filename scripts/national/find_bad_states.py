#!/usr/bin/env python3
"""Find rows in census-follow.csv where state is NOT a 2-letter code."""
import csv

with open("data/national/census-follow.csv", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    bad = 0
    good = 0
    for i, row in enumerate(reader):
        state = (row.get("state") or "").strip()
        if len(state) != 2 or not state.isalpha() or not state.isupper():
            if bad < 10:
                print(f"row {i}: state={state!r} county={row.get('county')!r} "
                      f"candidate_url={row.get('candidate_url')!r} "
                      f"vendor_family={row.get('vendor_family')!r} "
                      f"access_class={row.get('access_class')!r}")
            bad += 1
        else:
            good += 1
    print(f"\ngood state codes: {good}, bad: {bad}")
