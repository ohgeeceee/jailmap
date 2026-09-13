#!/usr/bin/env python3
"""Import official jail source leads into the discovery queue.

The importer is intentionally conservative: it validates the source-lead CSV and
updates records.county_ingestion_queue only as discovery metadata. It never
creates enabled jurisdictions and never writes booking records.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


REQUIRED_FIELDS = (
    "state",
    "county",
    "facility",
    "source_url",
    "source_owner",
    "source_kind",
    "access_status",
    "adapter_strategy",
    "publication_default",
    "evidence_url",
    "notes",
)

ALLOWED_PUBLICATION_DEFAULTS = {"staging_only", "blocked", "aggregate_only"}
ALLOWED_ACCESS_STATUSES = {
    "needs_research",
    "needs_adapter",
    "blocked",
    "active_staging",
    "no_public_source",
}


def canonical_county(value: str) -> str:
    normalized = value.strip().lower().replace("-", " ")
    if normalized.endswith(" county"):
        normalized = normalized[: -len(" county")]
    return " ".join(normalized.split())


def validate_https_url(value: str, field: str) -> str:
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError(f"{field} must be an HTTPS URL without embedded credentials")
    return value.strip()


def load_leads(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in REQUIRED_FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        leads = []
        seen = set()
        for line_number, row in enumerate(reader, start=2):
            lead = {field: (row.get(field) or "").strip() for field in REQUIRED_FIELDS}
            if len(lead["state"]) != 2 or not lead["state"].isupper():
                raise ValueError(f"Line {line_number}: state must be a two-letter uppercase code")
            for field in ("county", "facility", "source_owner", "source_kind", "notes"):
                if not lead[field]:
                    raise ValueError(f"Line {line_number}: {field} is required")
            lead["source_url"] = validate_https_url(lead["source_url"], "source_url")
            lead["evidence_url"] = validate_https_url(lead["evidence_url"], "evidence_url")
            if lead["access_status"] not in ALLOWED_ACCESS_STATUSES:
                raise ValueError(f"Line {line_number}: unsupported access_status")
            if lead["publication_default"] not in ALLOWED_PUBLICATION_DEFAULTS:
                raise ValueError(f"Line {line_number}: unsupported publication_default")
            key = (lead["state"], canonical_county(lead["county"]), lead["source_url"])
            if key in seen:
                raise ValueError(f"Line {line_number}: duplicate source lead")
            seen.add(key)
            leads.append(lead)
    return leads


def build_note(lead: dict[str, str]) -> str:
    note = (
        "Official source lead; not authorized for public ingestion. "
        f"Facility: {lead['facility']}. Owner: {lead['source_owner']}. "
        f"Kind: {lead['source_kind']}. Access: {lead['access_status']}. "
        f"Adapter strategy: {lead['adapter_strategy']}. "
        f"Publication default: {lead['publication_default']}. "
        f"Evidence: {lead['evidence_url']}. Notes: {lead['notes']}"
    )
    return note[:3000]


def import_leads(leads: list[dict[str, str]]) -> tuple[int, int]:
    from backend.db import pool

    imported = 0
    unmatched = 0
    with pool, pool.connection() as connection, connection.transaction():
        counties = connection.execute(
            '''SELECT c.id, c.name, s.abbrev FROM public."County" c
               JOIN public."State" s ON s.id = c."stateId"'''
        ).fetchall()
        lookup = {
            (row["abbrev"], canonical_county(row["name"])): row["id"]
            for row in counties
        }
        for lead in leads:
            county_id = lookup.get((lead["state"], canonical_county(lead["county"])))
            if not county_id:
                unmatched += 1
                continue
            updated = connection.execute(
                """UPDATE records.county_ingestion_queue
                   SET status = CASE
                       WHEN status IN ('source_discovery', 'blocked', 'no_local_jail')
                       THEN 'adapter_needed'
                       ELSE status
                     END,
                     source_url = COALESCE(source_url, %s),
                     adapter = COALESCE(adapter, %s),
                     notes = %s,
                     updated_at = now()
                   WHERE county_id = %s
                   RETURNING county_id""",
                (
                    lead["source_url"],
                    lead["adapter_strategy"],
                    build_note(lead),
                    county_id,
                ),
            ).fetchone()
            imported += int(updated is not None)
    return imported, unmatched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "official-jail-source-leads.csv",
        help="Path to the official source-lead CSV",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without database writes")
    args = parser.parse_args()

    leads = load_leads(args.csv)
    if args.dry_run:
        states = sorted({lead["state"] for lead in leads})
        print(f"Validated {len(leads)} official source leads across {len(states)} states: {', '.join(states)}")
        return 0
    imported, unmatched = import_leads(leads)
    print(f"Imported {imported} discovery leads; {unmatched} unmatched counties")
    return 1 if unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
