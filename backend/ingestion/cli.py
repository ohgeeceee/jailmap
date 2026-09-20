from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path

from .base import AdapterConfig
from .factory import build_adapter
from .models import BOOKING_JSON_SCHEMA
from .worker import ingest_records


def load_config(path: str) -> AdapterConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return AdapterConfig(**data)


def scaffold(args) -> int:
    config = {
        "facility_id": args.facility_id,
        "source_url": args.url,
        "state": args.state,
        "county": args.county,
        "vendor": args.driver,
        "timezone": args.timezone,
        "options": {"field_map": {"booking_number": "id", "first_name": "first_name", "last_name": "last_name", "booking_date": "booking_date"}},
    }
    Path(args.output).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return 0


def run(args) -> int:
    adapter = build_adapter(load_config(args.config))
    records = adapter.run()
    if args.summary_only:
        summary = {"facility_id": adapter.config.facility_id, "record_count": len(records), "database_writes": 0}
        if adapter.config.options.get("summarize_facilities"):
            summary["source_facilities"] = dict(Counter(
                str(record.raw_data.get("facility") or "unspecified") for record in records
            ).most_common(20))
        print(json.dumps(summary))
        return 0
    output = adapter.export(records, args.output)
    if not args.output:
        print(output)
    return 0


def ingest(args) -> int:
    if not args.commit:
        raise SystemExit("refusing database write without --commit")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    import psycopg

    adapter = build_adapter(load_config(args.config))
    records = adapter.run()
    with psycopg.connect(database_url) as connection:
        count = ingest_records(connection, records)
    print(json.dumps({
        "facility_id": adapter.config.facility_id,
        "records_staged": count,
        "publication_state": "staged",
    }))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.ingestion.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("scaffold", help="write a safe JSON adapter configuration")
    create.add_argument("--facility-id", required=True)
    create.add_argument("--url", required=True)
    create.add_argument("--driver", required=True)
    create.add_argument("--state")
    create.add_argument("--county")
    create.add_argument("--timezone", default="UTC")
    create.add_argument("--output", required=True)
    create.set_defaults(handler=scaffold)
    execute = subparsers.add_parser("run", help="run an adapter and export staged JSON")
    execute.add_argument("--config", required=True)
    execute.add_argument("--output")
    execute.add_argument("--summary-only", action="store_true", help="report a count without printing or saving records")
    execute.set_defaults(handler=run)
    database = subparsers.add_parser("ingest", help="fetch and transactionally upsert records into restricted staging")
    database.add_argument("--config", required=True)
    database.add_argument("--commit", action="store_true", help="required acknowledgement for a database write")
    database.set_defaults(handler=ingest)
    schema = subparsers.add_parser("schema", help="print the unified JSON Schema")
    schema.set_defaults(handler=lambda _: print(json.dumps(BOOKING_JSON_SCHEMA, indent=2)) or 0)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
