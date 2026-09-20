#!/usr/bin/env python3
"""Filter & normalize a leads CSV so it passes import_source_leads validation.
Fixes:
  - source_url must be https (promote http:// -> https://)
  - evidence_url must be https or empty; if empty, copy from source_url
  - ensure all required fields are populated
  - drop rows with non-URL source_url (placeholders like 'blocked' etc.)
"""
import argparse
import csv
import re
from pathlib import Path

URL_RE = re.compile(r'^https?://\S+', re.IGNORECASE)
HTTPS_RE = re.compile(r'^https://\S+', re.IGNORECASE)

FIELDS = [
    "state", "county", "facility", "source_url", "source_owner",
    "source_kind", "access_status", "adapter_strategy",
    "publication_default", "evidence_url", "notes",
]

ALLOWED_ACCESS = {"needs_research", "needs_adapter", "blocked", "active_staging", "no_public_source"}
ALLOWED_PUB = {"staging_only", "blocked", "aggregate_only"}


def normalize_url(raw):
    s = (raw or "").strip()
    if not s:
        return ""
    if HTTPS_RE.match(s):
        return s
    if URL_RE.match(s):
        return "https://" + s[7:]  # http -> https
    if "." in s and " " not in s:
        return "https://" + s
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    kept = 0
    dropped_bad_url = 0
    fixed_ev = 0
    fixed_http = 0

    with args.input.open(encoding="utf-8-sig", newline="") as incsv, \
         args.output.open("w", newline="") as outcsv:
        reader = csv.DictReader(incsv)
        writer = csv.DictWriter(outcsv, fieldnames=FIELDS)
        writer.writeheader()

        for row in reader:
            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip()
            facility = (row.get("facility") or "").strip()
            source_url = normalize_url(row.get("source_url", ""))
            evidence_url = normalize_url(row.get("evidence_url", ""))
            source_owner = (row.get("source_owner") or "").strip()
            source_kind = (row.get("source_kind") or "").strip()
            access_status = (row.get("access_status") or "").strip()
            adapter_strategy = (row.get("adapter_strategy") or "").strip()
            pub_default = (row.get("publication_default") or "").strip()
            notes = (row.get("notes") or "").strip()

            if not source_url:
                dropped_bad_url += 1
                continue

            if not HTTPS_RE.match(row.get("source_url", "") or ""):
                fixed_http += 1

            # evidence_url is required — fall back to source_url
            if not evidence_url:
                evidence_url = source_url
                fixed_ev += 1

            if not source_owner:
                source_owner = "county_sheriff"
            if not source_kind:
                source_kind = "html_roster"
            if access_status not in ALLOWED_ACCESS:
                access_status = "needs_adapter"
            if not adapter_strategy:
                adapter_strategy = "html_roster_staging"
            if pub_default not in ALLOWED_PUB:
                pub_default = "staging_only"

            writer.writerow({
                "state": state,
                "county": county,
                "facility": facility,
                "source_url": source_url,
                "source_owner": source_owner,
                "source_kind": source_kind,
                "access_status": access_status,
                "adapter_strategy": adapter_strategy,
                "publication_default": pub_default,
                "evidence_url": evidence_url,
                "notes": notes,
            })
            kept += 1

    print(f"Kept {kept}; dropped_bad_url {dropped_bad_url}; fixed_ev {fixed_ev}; fixed_http {fixed_http}")


if __name__ == "__main__":
    main()
