#!/usr/bin/env python3
"""Filter merged leads: drop rows with non-URL source_url and fix evidence_url."""
import csv
import re
from pathlib import Path

SRC = Path("data/national/official-jail-source-leads.csv")
DST = Path("data/national/official-jail-source-leads.csv")

URL_RE = re.compile(r'^https?://')

def is_url(s):
    return bool(URL_RE.match(s.strip()))

kept = []
dropped_url = 0
fixed_ev = 0

with SRC.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        if not is_url(row.get("source_url", "")):
            dropped_url += 1
            continue
        # evidence_url must also be a URL or empty
        ev = row.get("evidence_url", "")
        if ev and not is_url(ev):
            # crawl-log evidence isn't a URL — clear it or use source_url
            row["evidence_url"] = ""
            fixed_ev += 1
        kept.append(row)

with DST.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=kept[0].keys() if kept else [])
    writer.writeheader()
    writer.writerows(kept)

print(f"Kept: {len(kept)}")
print(f"Dropped (bad source_url): {dropped_url}")
print(f"Fixed (non-URL evidence_url): {fixed_ev}")
