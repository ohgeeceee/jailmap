# Modular roster adapters

This framework turns authorized public roster sources into a single validated JSON shape. It writes only to `records.adapter_bookings_staging`; it does not publish records or bypass the existing review/redaction pipeline.

## Lifecycle

Every driver implements `fetch()`, `parse()`, and `normalize()` through `BaseAdapter`. `run()` composes those stages, and `export()` produces JSON for inspection. Shared models reject missing identity keys, naive timestamps, implausible ages, and negative bond values.

Available driver names:

- `html_table` / `static_html`: ordinary server-rendered HTML tables.
- `php_table` / `synergistic`: aliases for configured server-rendered tables.
- `pdf_roster` / `static_pdf`: text PDFs parsed with a configured named-group regular expression.
- `json_api` / `rest_api` / `tyler_json`: bounded paginated JSON endpoints.
- `playwright_form` / `aspnet_form` / `jms_portal` / `smartcop`: public form or JavaScript flows rendered with Chromium.

Vendor names describe observed portal patterns, not guaranteed vendor APIs. VINE/Appriss is intentionally rejected unless JailMap has an authorized API agreement. Do not bypass CAPTCHAs, authentication, robots restrictions, or access controls.

## CLI

Create a JSON configuration:

```bash
python -m backend.ingestion.cli scaffold \
  --facility-id FACILITY_CUID \
  --url https://county.gov/roster \
  --driver html_table \
  --state MT --county Example --timezone America/Denver \
  --output example.json
```

Run it as an export-only dry run:

```bash
python -m backend.ingestion.cli run --config example.json --output staged-records.json
```

Use `--summary-only` for a source smoke test that reports only the record count and performs no database writes.

Print the canonical JSON Schema with `python -m backend.ingestion.cli schema`. Database ingestion is deliberately a separate call to `ingest_records(connection, records)` so a CLI typo cannot publish or mutate production.

After migration approval, an operator can stage a configured source with `python -m backend.ingestion.cli ingest --config example.json --commit`. The explicit flag is required, and all resulting rows retain the `staged` publication state.

## Database and operations

Apply `backend/migrations/20260920_adapter_ingestion.sql` only after an approved backup and release review. The upsert key is `(facility_id, booking_number)`. A newer scrape updates source-controlled fields while preserving `publication_state`, so re-ingestion cannot silently reapprove a suppressed or rejected record.

The default HTTP client identifies JailMap, throttles each adapter, follows redirects, and uses bounded retries for 429 and transient 5xx responses. It does not rotate identities. Playwright is isolated in `deploy/Dockerfile.ingestion`; the API image is not enlarged with Chromium.

Failure logging stores only stage, exception class, and a truncated safe message. Never include response bodies, source rows, DOBs, addresses, credentials, or tokens in exceptions or logs.
