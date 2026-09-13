# State / County / Jail / Ingestion

The authoritative hierarchy is PostgreSQL:

1. `public.State` has all 50 states.
2. `public.County` has Census 2025 counties and county equivalents, linked to states.
3. `public.Jail` holds verified facilities, linked to counties and states.
4. `records.jurisdictions` registers source URLs and adapter names. `jail_id` links
   a facility-specific source. County-wide feeds must not be assigned to a
   particular building without evidence.
5. `records.county_ingestion_queue` tracks discovery and implementation work.
6. `records.ingestion_runs` records source runs and safe error types.
7. `records.staged_bookings` is private working data. It is never searched or
   returned by the public booking endpoints.
8. `records.inmates` and its outbox are for reviewed, publishable booking data.

## Operator commands

```sh
cd /root/jailmap
python3 state_manager.py --status
python3 state_manager.py --list MT
python3 state_manager.py MT --dry-run
python3 state_manager.py GA
python3 state_manager.py --all --dry-run
systemctl status jailmap-ingest.timer
journalctl -u jailmap-ingest.service --no-pager -n 40
```

The timer runs daily at 12:15 UTC with up to five minutes jitter, after the
currently configured Fulton nightly feed refresh. Staging-only sources can run
while `enabled=false`, so they do not appear as public booking coverage.
Only `review_status=verified` sources run; `pending` is not authorization.
Source locks are taken before fetch. Every source commits separately. Failed
validation leaves its earlier data intact. Dry runs write neither bookings nor
run-history rows. Missing staging rows are removed from the staging snapshot;
missing public bookings are never automatically declared released.

## Add the next source

Work one state, then county, then verified facility at a time. Look up the
county FIPS in its state manifest, then update its queue status. Preserve
regional-jail and no-local-jail distinctions; geography is not evidence of a jail.

Use the official source's documented API or public roster. Record its source
reference and access conditions. Fetch within bounded size/time/page limits.
Implement a named adapter under backend/ and register it in backend.ingest.
Test stable booking identity, timezone, source freshness, complete pagination,
duplicate keys, custody status, adult eligibility, suppression, and failures.
Do not construct government URLs from county names.

Register the jurisdiction with publication disabled. For a feed that is not yet
publishable, use `staging_only=true`, preserve missing fields and quality flags,
and keep it out of `records.inmates`. A publishable source uses `staging_only=false`
and `enabled=true` only after the source-specific eligibility and contract are
verified. Standard JSON sources also need their exact SOURCE_ALLOWED_HOSTS entry.

Run --dry-run, review counts and quality flags, commit one state, then verify the
run, public API and search indexing as appropriate. Update the queue and state
progress report. Use source timestamps; do not relabel an old snapshot as fresh.

## Existing scaffold warning

The old /root/jailmap/states tree contains unfinished scripts and invalid county
names. It is preserved as prior work but is not executable coverage. The new
state_manager.py does not import those modules. Thirteen invalid Montana
jurisdictions are marked invalid_county and remain disabled for auditability.
The old setup_states.py is archived and replaced with a deprecation notice.

## Fulton County, Georgia

Source: https://sharefulton.fultoncountyga.gov/d/3vfv-9mmr
Attribution: Fulton County, Georgia. License: CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/).

The public dataset supplies name, booking number, date-only admission date and
gender. We omit gender. It does not supply adult eligibility, specific facility,
charges, or bonds. All records therefore remain private staging. The source
description says approximately 19:30 the previous evening, but eight rows in
the September 7 run have September 7 booking dates. Those rows retain a
booking_after_stated_snapshot quality flag. No timestamp is silently repaired.

The Main Jail directory entry comes from Georgia DOC:
https://gdc.georgia.gov/locations/fulton-county-jail
It is not used to assign all county roster entries to the Main Jail.
