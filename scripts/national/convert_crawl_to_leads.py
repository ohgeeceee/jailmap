#!/usr/bin/env python3
"""Convert crawl_sheriff_links output CSV to import_source_leads format."""
import argparse
import csv
from pathlib import Path


# crawl output columns:
# probed_at, state, county, jail, candidate_url, http_status, final_url,
# vendor_family, access_class, error, evidence, notes

# import columns:
# state, county, facility, source_url, source_owner, source_kind,
# access_status, adapter_strategy, publication_default, evidence_url, notes

ACCESS_MAP = {
    "html_roster": "needs_adapter",
    "pdf_roster": "needs_adapter",
    "search_form": "needs_adapter",
    "vendor_portal": "needs_adapter",
    "no_roster_found": "no_public_source",
    "blocked": "blocked",
    "needs_adapter": "needs_adapter",
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
}

STRATEGY_MAP = {
    "html_roster": "html_roster_staging",
    "pdf_roster": "pdf_roster_staging",
    "smartweb_portal": "smartweb_staging",
    "socrata_open_data_portal": "socrata_staging",
    "zuercher_portal": "zuercher_staging",
    "citizenrims_portal": "citizenrims_staging",
    "search_form": "search_form",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--access-class", nargs="+",
                        default=["html_roster", "pdf_roster", "vendor_portal",
                                 "smartweb_portal", "socrata_open_data_portal",
                                 "citizenrims_portal", "search_form"])
    args = parser.parse_args()

    out_fields = ["state", "county", "facility", "source_url", "source_owner",
                  "source_kind", "access_status", "adapter_strategy",
                  "publication_default", "evidence_url", "notes"]

    written = 0
    skipped = 0
    seen = set()

    with args.input.open(encoding="utf-8-sig", newline="") as incsv, \
         args.output.open("w", newline="") as outcsv:
        reader = csv.DictReader(incsv)
        writer = csv.DictWriter(outcsv, fieldnames=out_fields)
        writer.writeheader()

        for row in reader:
            access = (row.get("access_class") or "").strip()
            if access not in args.access_class:
                skipped += 1
                continue

            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip()
            facility = (row.get("jail") or "").strip()
            source_url = (row.get("final_url") or row.get("candidate_url") or "").strip()
            evidence_url = (row.get("evidence") or source_url).strip()
            notes = (row.get("notes") or "").strip()

            # skip rows where final_url is actually a crawl log artifact
            if source_url.startswith("https://www.") and "votes" in source_url:
                # these are election sites, not jail rosters
                if "roster" not in source_url.lower() and "inmate" not in source_url.lower() and "jail" not in source_url.lower():
                    skipped += 1
                    continue

            vendor = (row.get("vendor_family") or "").strip()
            source_kind = SOURCE_KIND_MAP.get(vendor, "html_roster")
            adapter_strategy = STRATEGY_MAP.get(vendor, "html_roster_staging")
            access_status = ACCESS_MAP.get(access, "needs_adapter")

            # dedupe
            key = (state, county.lower(), source_url)
            if key in seen:
                skipped += 1
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
                "publication_default": "staging_only",
                "evidence_url": evidence_url,
                "notes": notes,
            })
            written += 1

    print(f"Wrote {written} leads to {args.output}; skipped {skipped}")


if __name__ == "__main__":
    main()
