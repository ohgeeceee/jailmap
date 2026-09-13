# Hermes Bot Team for Jailmap

`hermes/jailmap-bots.yaml` defines the Jailmap operating team. It is a mission
contract, not an automatic production deployment.

## Operating Model

The team separates discovery, adapter implementation, privacy review, search
indexing, and production operations. Source scouts may add leads, but they may
not enable sources or publish records. Feed builders may create staging-only
adapters after review. Production operations require explicit approval.

## Source Intake Flow

1. A scout finds an official source and records it in
   `data/official-jail-source-leads.csv`.
2. The source importer validates the CSV shape and can write the lead into
   `records.county_ingestion_queue` as an unverified lead.
3. A privacy reviewer decides whether the source can become a staging-only feed.
4. A feed builder implements an adapter with bounded fetches, stable booking
   identity, duplicate detection, failure handling, and tests.
5. A human reviews source legality, eligibility, retention, correction workflow,
   and dry-run evidence before any public enablement.

## Commands

Validate the current lead file without touching the database:

```sh
cd /root/jailmap
python3 scripts/import_source_leads.py --dry-run
```

Import validated leads into the discovery queue:

```sh
cd /root/jailmap
python3 scripts/import_source_leads.py
```

Inspect national coverage:

```sh
cd /root/jailmap
python3 state_manager.py --status
python3 state_manager.py --list TX
```

Run an approved source only as a dry run:

```sh
cd /root/jailmap
python3 state_manager.py TX --county "Dallas" --dry-run
```

## Approval Gates

Human approval is required before:

- enabling any `records.jurisdictions` source;
- switching a source from `staging_only=true` to public ingestion;
- changing production timers, services, Docker, nginx, or DNS;
- deploying code to `jailmap.com`;
- bulk-exporting data or changing retention/correction policy.

## Lead Quality Standard

Each source lead must include state, county, facility, official source URL,
source owner, source kind, access status, adapter strategy, publication default,
evidence URL, and notes. Use `blocked` for captcha/login/terms barriers; do not
work around them.
