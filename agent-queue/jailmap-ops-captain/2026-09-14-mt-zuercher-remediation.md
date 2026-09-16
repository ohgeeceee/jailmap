# Draft — MT Zuercher source remediation

Date: 2026-09-14
Author: jailmap-ops-captain (Hermes)
Authority: MISSION.md Red tier — code change + `records.*` writes. **Not applied. Awaiting approval.**

## Summary

Coverage reads "27 enabled / 9 ingesting". Triage of the 27 shows only **14 are eligible to
ingest at all**, 8 of those work, and the rest are broken for two different reasons that need two
different responses. Separately, 5 of the 6 "failures" are not engineering failures at all.

| Bucket | Count | Meaning |
|---|---|---|
| Working | 8 | verified + last run succeeded |
| Recoverable | 1 | Gallatin — transient vendor maintenance |
| Dead at source | 5 | county disabled the public roster on its portal |
| Inert | 13 | enabled, but `review_status='unverified'` + `authorization_reference='pending'` |

## Evidence

### 1. Five sources: the county turned off public inmate search

`POST https://<host>/api/portal/inmates/load` returns **HTTP 404** for Carbon, Madison, Meagher,
Stillwater, Wheatland. Same path returns **HTTP 200 + 57 records** for Ravalli.

The portal advertises which modules a tenant has enabled:

```
GET /api/portal/config/enabled_pages

carbon-so-mt      -> ["landing_page","warrants","cfs","unit_statuses","current_cfs","submit_tip","attorney_case_view"]
stillwater-so-mt  -> ["landing_page","warrants","cfs","unit_statuses","current_cfs","attorney_case_view"]
ravalli-so-mt     -> ["landing_page","inmates","cfs","current_cfs"]     <-- works
```

`inmates` is absent for the failing tenants. The 404 is the correct behaviour of a tenant that has
disabled public inmate search. **No adapter change can fix this.** The roster is not published
there anymore.

### 2. Gallatin: vendor maintenance mode

```
POST .../api/portal/inmates/load
-> HTTP 200, content-type: text/html, 7047 bytes
-> <title>Zuercher Suite: Maintenance Mode</title>
```

The adapter calls `response.raise_for_status()` (passes — 200) then `response.json()` →
`JSONDecodeError`. This is **transient and self-healing**. It is currently indistinguishable from a
real parse failure in `records.ingestion_runs`, which makes the ingest health panel noisy.

### 3. Thirteen sources are structurally incapable of running

`backend/ingest.py:run()` selects `WHERE review_status='verified'`, so these are excluded before
the loop. They would also fail the explicit gate:

```python
if source['review_status'] != 'verified' or source['authorization_reference'].strip().lower() in ('', 'pending'):
    raise ValueError('Source authorization missing')
```

All 13 are `review_status='unverified'`, `authorization_reference='pending'`, `adapter='standard_json'`,
and `source_url` is a **county homepage** (e.g. `https://big-horn.mt.gov`, `https://granite.mt.gov`).
`standard_json` expects a paginated JSON `{items: [...]}` roster endpoint, not an HTML homepage. So
even with authorization fixed they would fail.

Counties: Big Horn, Blaine, Deer Lodge, Granite, Park, Phillips, Pondera, Powder River, Powell,
Roosevelt, Sanders, Sheridan, Teton.

### 4. Unrelated security finding

`backend/adapters/mt_zuercher.py:93` opens the client with `verify=False`, disabling TLS
certificate verification for every Zuercher fetch:

```python
with httpx.Client(timeout=45, follow_redirects=True, verify=False) as client:
```

## Proposed changes

### A. Adapter: detect vendor maintenance mode (code — Red)

`backend/adapters/mt_zuercher.py`, in the fetch loop:

```python
            response.raise_for_status()
            if 'text/html' in response.headers.get('content-type', ''):
                # Vendor serves a 200 HTML maintenance page. Surface it as a
                # distinct outcome instead of a JSON parse failure.
                if 'maintenance mode' in response.text.lower():
                    raise RuntimeError('Zuercher maintenance mode')
                raise RuntimeError('Zuercher returned HTML, not JSON')
            payload = response.json() or {}
```

Plus `backend/ingest.py` error classification so `RuntimeError('Zuercher maintenance mode')` records
`error_type='vendor_maintenance'` rather than an unhandled exception.

Requires `_assert_authorized` to accept the 404 case gracefully — see B.

### B. Data: disable the 5 dead sources (records.* write — Red)

```sql
-- reversible: record the prior state first
UPDATE records.jurisdictions
   SET enabled = false
 WHERE state='MT' AND county IN ('Carbon','Madison','Meagher','Stillwater','Wheatland')
   AND review_status='verified';
```

Recommend recording `review_status='blocked'` with a note that the county disabled public search,
so the state is legible later rather than looking like an oversight. Do **not** delete the rows —
if the county re-enables its portal, the source comes back.

### C. Data: resolve the 13 inert sources (records.* write — Red)

Two options, needs your call:

1. **Set `enabled=false`** on all 13. Honest immediately: "enabled" stops overstating coverage by
   13. They come back when a real source URL and authorization exist.
2. **Leave enabled, add a source URL and authorization per county.** That is real discovery work and
   belongs in the Week-1 plan, not a quick fix.

Recommendation: option 1 now (accuracy), option 2 as Day 4 work.

### D. Security: re-enable TLS verification (code — Red)

Drop `verify=False` from `mt_zuercher.py:93`. If a tenant has a genuinely broken cert, allowlist that
tenant explicitly rather than disabling verification globally.

## Rollback

- A/B/C are additive and reversible. Before B and C, snapshot:
  `docker compose exec -T postgres pg_dump -U jailmap_owner -d jailmap -t records.jurisdictions > /root/jailmap/backups/jurisdictions-$(date +%F).sql`
- Revert A and D via `git checkout backend/adapters/mt_zuercher.py backend/ingest.py`.
- Container rollback tags exist from the 2026-09-14 admin-panel deploy:
  `jailmap-api:rollback-20260914-034047`, `jailmap-web:rollback-20260914-034047`.

## What this changes for the coverage number

Current: 27 enabled, 9 ingesting.

After A–C: **14 enabled, 8 ingesting + 1 recoverable.** The number goes *down*, and that is the
point — 13 sources that can never run stop counting as coverage. Real growth then comes from the
Week-1 plan (`docs/national-rollout-plan.md`), starting with the 3,504 jails that have no
identified source at all.

## Approval needed

- [ ] A — adapter maintenance-mode detection + ingest error classification
- [ ] B — disable the 5 county-disabled sources
- [ ] C — disable (or resolve) the 13 inert sources
- [ ] D — remove `verify=False`
