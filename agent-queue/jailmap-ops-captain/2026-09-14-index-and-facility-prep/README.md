# Draft — Day 3 index + facility prep

Date: 2026-09-14
Author: jailmap-ops-captain (Hermes)
Authority: MISSION.md Red tier — application code + schema change + container rebuild.
**Not applied. Awaiting approval.**

Full evidence for everything below: `docs/day1-findings.md`.

---

## Summary

Three changes, in dependency order. A is safe and immediate; B is the architectural prerequisite;
C is the volume work that only becomes possible after B.

| | Change | Tier | Risk |
|---|---|---|---|
| **A** | Stop prerendering the sitemap; log the failure instead of swallowing it | Red (code + rebuild) | Low — reversible, no schema, no data |
| **B** | `records.facility_jurisdiction_map` + county-name normalizer | Red (schema) | Low — additive table, no destructive change |
| **C** | Enrich `directory_enrichment_queue` → contact/custodian data → facility pages | Red (data + code) | Medium — 3,143 rows of real work, gated on content |

---

## A. Sitemap fix

**Problem.** `src/app/sitemap.ts` is prerendered during `docker build`, where `DATABASE_URL` is
unset. `src/lib/prisma.ts` throws `Map database is not configured`. The bare `try {} catch {}`
swallows it. Result: a frozen 54-URL `sitemap.xml.body` inside the image, 0 county URLs, and Google
has never been told a single county page exists. Verified: the body's mtime does not change when the
route is requested.

**Proposed:** `sitemap.ts.proposed` in this directory. Four changes:

1. `export const dynamic = 'force-dynamic'` — the route must query at request time. Its entire job
   is to reflect live coverage, so a cached artifact is wrong by construction. The fix must not
   depend on whether ISR happens to fire while `DATABASE_URL` is present.
2. Replace the silent `catch` with a logged one. Keep the route from 500-ing (that was the original
   intent and it is correct) but make the failure visible:
   `console.error('[sitemap] county query failed:', error)`.
3. Add `/leaderboard` and `/new-bookings` — both serve 200 today and neither is discoverable.
4. Emit county URLs from `records.jurisdictions WHERE enabled` **plus** counties that have verified
   facility contact data, and leave facility URLs out until B and C land.

**Expected immediate effect:** the sitemap goes from 54 URLs to ~80 (50 states + 3 static + 2 new +
26 enabled counties). Small, but it is the first time the highest-value pages are announced.

**Not in scope:** facility URLs. They stay out until the bridge exists, so the sitemap never
advertises thin pages.

---

## B. The facility↔jurisdiction bridge

**Problem.** The national directory and the ingestion registry have no key between them.

- `public."Jail".id` = `census-landmark-<OID>`, 3,531 rows, sourced from Census TIGERweb landmarks.
- `records.facility_sources` is keyed on that same id and every `source_url` is a TIGERweb geometry
  query — it is a geographic registry, not a roster registry.
- `records.jurisdictions` is a UUID keyed by `(state, county)`, with no column pointing at the
  directory.
- Matching on (state, normalized county, name-slug) yields **3 matches out of 3,531**.

So "which jail is this, and is it ingesting?" is currently unanswerable at facility granularity.
That blocks facility pages, blocks per-facility FOIA tracking, and blocks per-facility coverage
reporting.

**Proposed:** `sql/facility-jurisdiction-map.sql` in this directory.

- New table `records.facility_jurisdiction_map(jail_id PK → public."Jail", jurisdiction_id →
  records.jurisdictions, match_method, match_confidence, reviewed_by, reviewed_at, notes)`.
- Additive only. No existing table altered, no column dropped, no row updated.
- Seed with the 3 automatic matches at `match_confidence = 1.00`, `match_method = 'name_exact'`.
- Everything else is inserted as `match_method = 'unmatched'` so the remainder is a *visible work
  queue* rather than an unknown.

**Why a separate table and not a column on `jurisdictions`:** one jurisdiction may cover several
facilities (county jails with multiple facilities), and one facility may be covered by a state-level
source. A many-to-many-capable map reflects that. A `census_landmark_id` column on
`jurisdictions` would encode a one-to-one assumption that the data does not support.

`county-slug.ts.proposed` carries the normalizer. The trap it fixes:

```
public."County".name        = "Flathead County"
records.jurisdictions.county = "Flathead"
```

Every join or slug built without stripping the trailing `" County"` fails silently. The existing
`slugifyCounty` in `county/[state]/[county]/page.tsx` does not strip it. Existing URLs
(`/county/MT/flathead`) remain valid after the fix — no redirect needed.

---

## C. Enrichment, then facility pages

**Reality check on the directory.** `public."Jail"` has `website` on all 3,531 rows, but 3,528 are
TIGERweb geometry queries. Address is populated on **7** rows, phone on **3**.
`records.facility_contact_details` has **3** rows. `records.directory_enrichment_queue` has **3,143**
unworked rows.

Facility pages built from the directory today would carry a name, a county, sometimes a city, and a
map point. Publishing that 3,531 times is a thin-content liability, not an SEO win.

**Proposed order:**

1. Work `directory_enrichment_queue` for a first tranche (~25–50 counties, highest jail counts
   first): find the official sheriff/county corrections page, extract address, phone, contact page.
   Populate `facility_contact_details` with `verified_at` set.
2. **Extract the records custodian name and email from the same pages.** This is the second payoff:
   the FOIA pipeline needs exactly this and it is already on the page you are reading.
3. Ship facility pages only for facilities with verified contact data, gated in the query — never
   from raw directory rows.

**Slug disambiguation:** `"Franklin County Jail"` appears three times with distinct landmark ids. The
slug must be `slugify(name)` with a short landmark-id suffix on collision, or the route collides.

---

## Files in this draft

| File | What it is |
|---|---|
| `sitemap.ts.proposed` | Full replacement for `src/app/sitemap.ts` |
| `county-slug.ts.proposed` | New `src/lib/county-slug.ts`, shared normalizer |
| `sql/facility-jurisdiction-map.sql` | Additive migration + automatic-match seed |
| `sql/verify.sql` | The queries that prove each change worked |

These are drafts. They have not been type-checked or built, because building is part of the change.
On approval the sequence is: copy files into place, `npx tsc --noEmit -p tsconfig.json`,
`npm run build`, then `docker compose build api web && docker compose up -d api web`.

---

## Rollback

- **A:** `git checkout src/app/sitemap.ts` then rebuild. No data touched.
- **B:** `DROP TABLE records.facility_jurisdiction_map;` — it is referenced by nothing. No existing
  table is altered by the migration, so rollback is exact.
- **C:** enrichment writes are row-scoped and reversible (`DELETE FROM
  records.facility_contact_details WHERE verified_at >= '<date>'`); the queue itself is never
  deleted, only marked.
- Container rollback tags exist from the 2026-09-14 deploy:
  `jailmap-api:rollback-20260914-034047`, `jailmap-web:rollback-20260914-034047`.
- Snapshot before B and C:
  `docker compose exec -T postgres pg_dump -U jailmap_owner -d jailmap -t records.facility_contact_details > /root/jailmap/backups/fcd-$(date +%F).sql`

---

## Verification

```bash
cd /root/jailmap

# A — the sitemap must announce county pages, and must do it from the live DB
curl -s https://jailmap.com/sitemap.xml | grep -c 'county/'
curl -s https://jailmap.com/sitemap.xml | grep -oE '<loc>[^<]+' | wc -l
# before: 0 county URLs / 54 total.  after: == count of content-eligible counties / ~80 total

# A — and it must still not 500 if the DB blips (the original guard's intent, preserved)
docker compose logs web --tail 50 | grep '\[sitemap\]' || echo 'no sitemap errors logged'

# B — the bridge exists and the remainder is visible, not unknown
docker compose exec -T postgres psql -U jailmap_owner -d jailmap -c \
  "SELECT match_method, count(*) FROM records.facility_jurisdiction_map GROUP BY 1 ORDER BY 2 DESC;"

# C — facility pages exist only where enrichment is verified
docker compose exec -T postgres psql -U jailmap_owner -d jailmap -c \
  "SELECT count(*) AS verifiable_facilities FROM records.facility_contact_details WHERE verified_at IS NOT NULL;"
```

---

## Approval needed

- [x] **A** — sitemap: force-dynamic, logged failure, add /leaderboard + /new-bookings
      **APPLIED 2026-09-14 and verified** — 54 → 83 URLs, 0 → 27 county URLs, all 200.
      Rollback: `jailmap-web:rollback-sitemap-20260914-050306` +
      `backups/sitemap.ts.bak-20260914-050306`.
- [x] **A2** — content gate **APPLIED 2026-09-14 and verified** — sitemap trimmed 27 → 8 county
      URLs; the 19 empty shells are no longer advertised (they still serve 200 directly, just
      unlisted). Gated on `EXISTS (SELECT 1 FROM records.inmates WHERE jurisdiction_id = j.id AND
      visibility = 'public')` — content, not the `enabled` flag.
      Rollback: `jailmap-web:rollback-contentgate-20260914-051014` +
      `backups/sitemap.ts.precontentgate-20260914-051014`.
- [x] **A3** — grant drift **APPLIED 2026-09-14 and verified** —
      `GRANT SELECT ON records.facility_contact_details TO jailmap_app;` run as `jailmap_owner`.
      Before: `ERROR: permission denied for table facility_contact_details`. After: `SET ROLE
      jailmap_app; SELECT count(*) ...` returns 3. Survives container recreation (it is a DB-level
      grant, not container state). Rollback: `REVOKE SELECT ON records.facility_contact_details
      FROM jailmap_app;`
- [ ] **B** — `records.facility_jurisdiction_map` migration + 3-row automatic seed
- [ ] **C** — enrichment tranche 1 (25–50 counties) + custodian-contact extraction + gated facility pages
- [ ] Rebuild `web` (and `api` if the enrichment writer lives there) — separate explicit go

Note: `compose.override.yaml` hardcodes the image tags, so `RELEASE_TAG` is ignored and every build
overwrites the tag the running container points at. Tag a rollback image before each deploy.
