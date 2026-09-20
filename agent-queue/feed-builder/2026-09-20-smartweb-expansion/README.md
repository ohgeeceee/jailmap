# SmartWEB adapter expansion checkpoint

Status: `ADAPTER_HARDENED_LOCALLY / SOURCES_NEED_COMPLETE-ROSTER CONTRACT`

## Adapter work completed

`backend/adapters/fl_smartweb.py` now:

- uses normal TLS certificate verification;
- parses Florida source timestamps in `America/New_York`;
- rejects unknown custody status and invalid booking dates;
- requires an adult-eligibility age and excludes rows below 18;
- rejects duplicate booking numbers;
- stops inventing placeholder charges and timestamps;
- continues to exclude mugshot URLs.

The focused and shared parser suite passes. A live Putnam County no-write dry run returned the same
one-record count from both the deployed and hardened adapters at the time of comparison.

## Official endpoints checked on 2026-09-20

| County | Result | Next action |
| --- | --- | --- |
| Bradford | gateway failure | retry later; do not increase request frequency |
| Escambia | reachable SmartWEB | implement complete current-custody search and pagination |
| Glades | reachable SmartWEB | same |
| Hamilton | reachable SmartWEB | same |
| Sumter | reachable SmartWEB | same; add host only after source review |
| Suwannee | reachable SmartWEB | same; add host only after source review |

## Blocking vendor behavior

The initial `jail.aspx` response is a recent-bookings/default view. It is not proof of the complete
current inmate population. SmartWEB exposes “Current Inmates Only” through an ASP.NET form and
loads additional result batches through `Jail.aspx/AddMoreResults`. Vendor versions use at least
two request/response shapes. A source must not be registered merely because the landing page parses.

The next implementation must:

1. establish a cookie-preserving session;
2. submit the current-inmates-only search rather than relying on the default landing view;
3. consume every `AddMoreResults` batch with a strict page/row/time bound;
4. support both observed vendor JSON envelopes explicitly;
5. reject partial pagination, count mismatches, duplicates, and unknown response shapes;
6. retain only the fields allowed by JailMap’s public projection;
7. pass an official-source dry run independently for each county;
8. keep every new county disabled and staging-only pending human review.

No new SmartWEB jurisdiction was registered or published in this pass.
