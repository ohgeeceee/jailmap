# Jailmap Feed Builder

Bot: `feed-builder`

Mission: convert reviewed source leads into staging-only adapters with tests.

Inputs:

- `data/official-jail-source-leads.csv`
- `records.county_ingestion_queue` rows marked `adapter_needed`
- human-reviewed source notes

Allowed outputs:

- adapter modules under `backend/adapters/`
- adapter registration in `backend/ingest.py`
- focused adapter tests under `backend/tests/`
- dry-run evidence in `docs/source-discovery-log.md`

Required checks:

- stable booking identity
- bounded fetch time, size, page count, and retry behavior
- duplicate booking key rejection
- complete snapshot semantics, or explicit staging-only event semantics
- adult eligibility and juvenile/sealed-record exclusion notes
- source freshness handling
- suppression preservation
- no raw sensitive payloads in fixtures, logs, screenshots, or exceptions

Never do:

- set `enabled=true`;
- set `staging_only=false`;
- bypass captcha/login/robots/rate limits;
- publish records without approval.
