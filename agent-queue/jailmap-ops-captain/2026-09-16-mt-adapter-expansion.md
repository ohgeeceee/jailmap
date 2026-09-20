# Draft — JailMap MT adapter expansion + Zuercher remediation

Date: 2026-09-16
Author: jailmap-ops-captain (Hermes)
Authority: MISSION.md Red tier — code change + `records.*` writes + rebuild. **Not applied. Awaiting approval.**

## Summary

Two new MT county adapters written, tested (12/12 passing), and registered in `backend/ingest.py`. Also identifies 5 dead Zuercher sources for disabling.

| Change | Type | Status |
|---|---|---|
| `backend/adapters/mt_prairie.py` — new adapter | Code (Red) | Written, tested |
| `backend/adapters/mt_lake.py` — new adapter | Code (Red) | Written, tested |
| `tests/test_mt_prairie.py` — tests | Code (Red) | Written, 7/7 passing |
| `tests/test_mt_lake.py` — tests | Code (Red) | Written, 5/5 passing |
| `backend/ingest.py` — register adapters | Code (Red) | Patched |
| Disable 5 dead Zuercher sources | DB write (Red) | Drafted below |
| Reapi api container to pick up new code | Deploy (Red) | Needs approval |

## New adapters

### Prairie County (`mt_prairie.py`)
- Source: `https://www.myr2m.com/PrairieCoRoster/NewInmates.aspx`
- Pure HTML roster (ASP.NET WebForms), no auth/captcha
- All fields in indexed `<span>` tags — parseable with stdlib
- Data: name, sex, race, age, address, booking date, agency, release date, charges

### Lake County (`mt_lake.py`)
- Source: `https://www.lakemt.gov/DocumentCenter/View/816/Jail_Roster-?bidId=`
- Text-based PDF (not table-based), refreshed regularly
- Uses pdfplumber (already in container)
- Data: name, jacket #, age, race, sex, days, booking date, agency, charges

## DB changes needed

### Update adapter + source_url for PENDING-ADAPTER counties

```sql
-- Prairie: was PENDING-ADAPTER, now points to real roster
UPDATE records.jurisdictions
   SET adapter='prairie_html_staging',
       source_url='https://www.myr2m.com/PrairieCoRoster/NewInmates.aspx',
       staging_only=true,
       review_status='verified',
       authorization_reference='public_web_roster_20260916'
 WHERE state='MT' AND county='Prairie';

-- Lake: was PENDING-ADAPTER, now points to real roster
UPDATE records.jurisdictions
   SET adapter='lake_pdf_staging',
       source_url='https://www.lakemt.gov/DocumentCenter/View/816/Jail_Roster-?bidId=',
       staging_only=true,
       review_status='verified',
       authorization_reference='public_pdf_roster_20260916'
 WHERE state='MT' AND county='Lake';
```

### Disable 5 dead Zuercher sources

Counties Carbon, Madison, Meagher, Stillwater, Wheatland all return HTTP 404 on `/api/portal/inmates/load` because the county disabled public inmate search on its portal (confirmed via `GET /api/portal/config/enabled_pages` — `inmates` absent).

```sql
UPDATE records.jurisdictions
   SET enabled=false,
       staging_only=false,
       review_status='blocked',
       authorization_reference='county_disabled_public_search_20260916'
 WHERE state='MT' AND county IN ('Carbon','Madison','Meagher','Stillwater','Wheatland')
   AND review_status='verified';
```

### Ensure SOURCE_ALLOWED_HOSTS covers new adapters

`.env` already has `www.myr2m.com` and `www.lakemt.gov` in the allowlist. No change needed.

## Required deploy steps

```bash
cd /root/jailmap
docker compose build api
docker compose up -d --no-deps api
```

## Rollback

- Revert all files via `git checkout`
- For DB: re-enable the 5 counties and revert adapter/source_url for Prairie/Lake
- Container rollback tag from today: `jailmap-api:rollback-<prev-timestamp>`

## What this changes for coverage

Current (verified): MT 5 counties ingesting (Flathead, Jefferson, Missoula, Ravalli, Yellowstone)

After applying:
- MT 5 still ingesting (the working ones)
- MT 2 staging (Prairie, Lake) — producing data, not public
- 5 dead sources blocked instead of failing daily

When Prairie/Lake staging looks clean, promote to public ingestion via separate approval.

## Approval needed

- [ ] A — Apply DB updates (Prairie/Lake adapter+url, disable 5 dead)
- [ ] B — Rebuild api container to register new adapters
- [ ] C — Run Prairie/Lake adapters in dry-run first to validate

## National census results (2,648 candidates probed)

| Access class | Count | Meaning |
|---|---|---|
| no_roster_found | 1,348 | Homepage has no roster link |
| search_form | 426 | Search form exists (needs outreach) |
| unreachable | 289 | Domain doesn't resolve |
| blocked | 256 | HTTP 403/406 (WAF, rate limit) |
| login_required | 89 | Login wall |
| captcha_gated | 83 | CAPTCHA |
| robots_disallowed | 52 | robots.txt blocks |
| vendor_portal | 44 | Vendor portal (Zuercher, etc.) |
| html_roster | 19 | Direct HTML roster |
| pdf_roster | 2 | PDF roster |

**Ingest candidates (vendor_portal + html_roster + pdf_roster): 65 of 2,648 (2.5%)**

This confirms the skill's ceiling: ~290 ingest candidates nationally, not thousands. The path forward is vendor family adapters (Zuercher, Tyler, SmartWEB) and FOIA outreach for the 426 search_form counties.
