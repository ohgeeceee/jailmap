#!/usr/bin/env python3
"""Convert crawl output (source-census.csv or census-follow.csv) to leads format.

Input columns:
  probed_at, state, county, jail, candidate_url, http_status, final_url,
  vendor_family, access_class, error, evidence, notes

Two files use these columns differently:
  - source-census.csv: access_class carries the source type (search_form, html_roster, etc.),
    vendor_family is mostly empty.
  - census-follow.csv: access_class = publication_default ("staging_only"/"no_roster_found"),
    vendor_family carries the real source type.

This converter handles both: the effective source type is vendor_family when set,
otherwise access_class when it indicates a real source.
"""
import argparse
import csv
import re
from pathlib import Path

URL_RE = re.compile(r'^https?://\S+', re.IGNORECASE)

ACCESS_MAP = {
    "html_roster": "needs_adapter",
    "pdf_roster": "needs_adapter",
    "search_form": "needs_adapter",
    "vendor_portal": "needs_adapter",
    "smartweb_portal": "needs_adapter",
    "socrata_open_data_portal": "needs_adapter",
    "zuercher_portal": "needs_adapter",
    "citizenrims_portal": "needs_adapter",
    "tyler_jailtracker_portal": "needs_adapter",
    "tyler_odyssey_portal": "needs_adapter",
    "no_roster_found": "no_public_source",
    "blocked": "blocked",
    "login_required": "blocked",
    "captcha_gated": "blocked",
    "staging_only": "needs_adapter",
    "manual_discovery": "needs_research",
}

SOURCE_KIND_MAP = {
    "html_roster": "html_roster",
    "pdf_roster": "pdf_roster",
    "search_form": "search_form",
    "vendor_portal": "vendor_portal",
    "smartweb_portal": "vendor_portal",
    "socrata_open_data_portal": "vendor_portal",
    "zuercher_portal": "vendor_portal",
    "citizenrims_portal": "vendor_portal",
    "tyler_jailtracker_portal": "vendor_portal",
    "tyler_odyssey_portal": "vendor_portal",
}

STRATEGY_MAP = {
    "html_roster": "html_roster_staging",
    "pdf_roster": "pdf_roster_staging",
    "smartweb_portal": "smartweb_staging",
    "socrata_open_data_portal": "socrata_staging",
    "zuercher_portal": "zuercher_staging",
    "citizenrims_portal": "citizenrims_staging",
    "tyler_jailtracker_portal": "tyler_staging",
    "tyler_odyssey_portal": "tyler_staging",
    "search_form": "search_form",
}

VALID_SOURCES = {
    "html_roster", "pdf_roster", "search_form", "vendor_portal",
    "smartweb_portal", "socrata_open_data_portal", "zuercher_portal",
    "citizenrims_portal", "tyler_jailtracker_portal", "tyler_odyssey_portal",
}

PUBLICATION_DEFAULTS = {
    "staging_only", "no_roster_found", "blocked", "login_required", "captcha_gated",
}


def normalize_url(raw):
    s = (raw or "").strip()
    if not s:
        return ""
    if URL_RE.match(s):
        return s
    if "." in s and " " not in s:
        return "https://" + s
    return ""


def classify(row):
    """Return (vendor, pub_default) — the effective source type and publication default."""
    vendor = (row.get("vendor_family") or "").strip()
    access = (row.get("access_class") or "").strip()

    if vendor in VALID_SOURCES:
        # census-follow style: vendor_family = source type, access_class = pub default
        if access in PUBLICATION_DEFAULTS:
            return vendor, access
        return vendor, "staging_only"

    # source-census style: access_class carries the source type
    if access in VALID_SOURCES:
        pub = access if access in PUBLICATION_DEFAULTS else "staging_only"
        return access, pub

    return "", ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    out_fields = ["state", "county", "facility", "source_url", "source_owner",
                  "source_kind", "access_status", "adapter_strategy",
                  "publication_default", "evidence_url", "notes"]

    written = 0
    skipped_no_source = 0
    skipped_no_url = 0
    seen = set()

    with args.input.open(encoding="utf-8-sig", newline="") as incsv, \
         args.output.open("w", newline="") as outcsv:
        reader = csv.DictReader(incsv)
        writer = csv.DictWriter(outcsv, fieldnames=out_fields)
        writer.writeheader()

        for row in reader:
            vendor, pub_default = classify(row)
            if not vendor:
                skipped_no_source += 1
                continue

            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip()
            facility = (row.get("jail") or "").strip()
            candidate_url_raw = (row.get("candidate_url") or "").strip()
            final_url_raw = (row.get("final_url") or "").strip()
            evidence = (row.get("evidence") or "").strip()
            notes = (row.get("notes") or "").strip()

            source_url = ""
            for u in (final_url_raw, candidate_url_raw):
                source_url = normalize_url(u)
                if source_url:
                    break
            if not source_url:
                skipped_no_url += 1
                continue

            evidence_url = normalize_url(evidence)

            source_kind = SOURCE_KIND_MAP.get(vendor, "html_roster")
            adapter_strategy = STRATEGY_MAP.get(vendor, "html_roster_staging")
            access_status = ACCESS_MAP.get(vendor, "needs_adapter")

            # normalize publication_default
            if pub_default in ("no_roster_found", "blocked", "login_required", "captcha_gated"):
                pub = "blocked"
            elif pub_default == "staging_only":
                pub = "staging_only"
            else:
                pub = "staging_only"

            key = (state, county.lower(), source_url)
            if key in seen:
                skipped_no_source += 1
                continue
            seen.add(key)

            writer.writerow({
                "state": state,
                "county": county,
                "facility": facility,
                "source_url": source_url,
                "source_owner": vendor or "county_sheriff",
                "source_kind": source_kind,
                "access_status": access_status,
                "adapter_strategy": adapter_strategy,
                "publication_default": pub,
                "evidence_url": evidence_url,
                "notes": notes,
            })
            written += 1

    print(f"Wrote {written} leads; skipped_no_source {skipped_no_source}; skipped_no_url {skipped_no_url}")


if __name__ == "__main__":
    main()
