# JailMap — Day 1 findings

Date: 2026-09-14
Author: Hermes (jailmap-ops-captain), Green-tier investigation. **Nothing changed.**
Scope: fresh coverage audit, sitemap root cause, Day-3 preparation.

---

## 1. Coverage audit — fresh run confirms the baseline, unchanged

`./scripts/national/run.sh audit_coverage.py --markdown` re-run today:

| Metric | Value |
|---|---|
| Jails in directory | 3,531 |
| Jails with a real jurisdiction site | 7 |
| Counties in directory | 3,143 |
| Registered jurisdictions | 51 |
| Enabled for ingestion | 27 |
| **Ingesting in the last 7 days** | **9** |
| Coverage of jails | 0.25% |
| Booking records | 4,879 (4,617 public) |
| `states/**/adapter.py` raising `NotImplementedError` | 2,947 of 2,978 |
| `backend/adapters/` files | 42 |

By state: MT 45 registered / 24 enabled / 5 live · ID 3 / 2 / 2 · GA 2 / 1 / 2 · SD 1 / 0 / 0.

No drift from the plan's baseline. The only four states with any registered jurisdiction are still
MT, ID, GA, SD.

---

## 2. Sitemap defect — root cause identified, evidence complete

**The sitemap is a frozen build artifact. It never queries the database in production.**

Evidence chain:

| Step | Evidence |
|---|---|
| The served sitemap is a static file | `/app/.next/server/app/sitemap.xml.body` — 54 `<loc>` entries, **0** matching `county/`, mtime `2026-09-14 04:47:17` = image build time |
| It is registered as prerendered | `sitemap.xml.meta` → `cache-control: public, max-age=0, must-revalidate`, `x-next-cache-tags: _N_T_/sitemap.xml/route` |
| Requesting it does not regenerate it | `curl` the route → HTTP 200, body mtime unchanged at `04:47:17` |
| The build has no database | `deploy/Dockerfile.web` build stage runs `npm run build`; `DATABASE_URL` is supplied by compose at **container runtime**, not at build time |
| Code throws when the DB is unset | `src/lib/prisma.ts`: `if (!process.env.DATABASE_URL) throw new Error('Map database is not configured')` |
| The throw is swallowed | `src/app/sitemap.ts` wraps the county query in a bare `try {} catch {}` with no logging |
| The runtime query path works fine | `curl /state/MT` renders **24** `/county/MT/...` links from `records.jurisdictions` at request time |
| It is not an adapter/dependency problem | `PrismaPg` is bundled into `/app/.next/server/chunks/_06d27up._.js` |

**Mechanism:** a guard written for "the records schema is briefly unavailable" silently converted a
build-environment limitation into a permanently wrong sitemap. Google has never been told about a
single county page.

Impact:

- 54 URLs submitted instead of 26 counties + 50 states + static.
- `/leaderboard` and `/new-bookings` return 200 and are absent from the sitemap entirely.
- The sitemap can only self-heal if the ISR window fires while `DATABASE_URL` is present; that is
  unverified, and a build-time-frozen asset is the wrong architecture for a route whose whole job
  is to reflect live coverage. **Fix must not depend on ISR timing.**

---

## 3. The Day-3 blocker: the directory and the ingestion side do not join

This is the finding that changes the plan.

The national directory and `records.jurisdictions` are two disconnected universes with no key
between them.

| Thing | Key | Count |
|---|---|---|
| `public."Jail"` | `id = 'census-landmark-<12-digit OID>'` | 3,531 |
| `records.facility_sources` | PK `jail_id` → FK `"Jail"(id)`; every `source_url` is a **TIGERweb geometry query** | 3,531 |
| `records.jurisdictions` | UUID, keyed by `(state, county)` — **no FK to the directory** | 51 |
| Facilities matching a jurisdiction on (state, normalized county, name slug) | — | **3 of 3,531** |

The three matches are incidental name collisions, not a designed mapping. The real-world mismatch:

```
directory      "Flathead County Justice Ctr"          jurisdiction   (no matching row)
directory      "Yellowstone County Detention Faclty"  jurisdiction   (no matching row)
directory      "Fulton County Jail - Main Jail"        jurisdiction   "Fulton County public jail roster (facility not specified)"
directory      "Bonneville County Jail"                jurisdiction   "Bonneville County Jail"   <-- matches
```

Two additional traps:

- **County naming differs between the two sides.** Directory `public."County".name` is
  `"Flathead County"`; `records.jurisdictions.county` is `"Flathead"`. Any join that does not strip
  the trailing `" County"` fails silently.
- **The directory contains duplicate names.** `SELECT name FROM public."Jail"` shows
  `"Franklin County Jail"` three times with three different landmark ids. A name-based URL slug will
  collide; slugs need disambiguation.

### Consequence

A facility page that wants to show *"this jail ingests, here is its roster status, here is its
records-request status"* requires a **mapping table that does not exist**. Building facility pages
before that mapping means shipping 3,531 thin pages that duplicate their county page and link
nowhere useful.

**So the prerequisite is the bridge, not the pages.** That reorders Day 3.

---

## 4. Directory metadata reality — the SEO volume is not there yet

Measured on `public."Jail"`:

| Field | Populated |
|---|---|
| `website` | 3,531 — but 3,528 are Census TIGERweb geometry queries, not real sites |
| `latitude` | 3,528 |
| `address` | **7** |
| `phone` | **3** |
| `records.facility_contact_details` rows | **3** (each with real `source_url`, `contact_url`, and a keyed `department_phones` object: `records`, `bonds_and_dockets`, `visitation_front_desk`, `visitation_appointments`) |
| `records.directory_enrichment_queue` rows | **3,143** (unworked) |

A facility page built from the directory today carries: name, city (sometimes), county, state, and
a map point. That is thin content — the kind Google disregards and the kind that gets a site
demoted when published at 3,531-page scale.

**The volume unlock is enrichment, not publication.** And the enrichment has a second payoff: the
same official page that yields a facility address and phone yields the **records custodian name and
email** the FOIA pipeline needs. One workstream feeds both engines.

---

## 5. Revised Day 3

| Original Day 3 | Revised Day 3 |
|---|---|
| Ship facility pages from directory rows | **Fix the sitemap** (unlocks the 26 existing county pages immediately, measured) |
| Assume directory = indexable content | **Build the facility↔jurisdiction bridge** (`records.facility_jurisdiction_map`) + county-name normalizer |
| 100 new facility pages return 200 | **Work `directory_enrichment_queue`** for the first N counties: official source → contact data → custodian contact. Facility pages ship only where enrichment exists, gated on content |
| — | Publish `/county/[state]/[county]` for every county with **live data or verified enrichment** — never on directory rows alone |

Exit criterion changes from "100 pages return 200" to:

1. `curl -s https://jailmap.com/sitemap.xml | grep -c 'county/'` returns a number greater than 0 and
   equal to the count of content-eligible counties.
2. The bridge exists, is seeded with the 3 automatic matches, and lists the unmatched remainder.
3. Enrichment has run for ≥25 counties with `verified_at` set, and facility pages exist only for
   those.

---

## 6. Standing items untouched today

- The MT Zuercher remediation draft (`2026-09-14-mt-zuercher-remediation.md`) remains unapplied —
  4 Red-tier items awaiting approval.
- `jailmap-ingest.service` still failed; `jailmap-wa-ingest.service` still failing.
- `docs/coverage-baseline.md` regenerates identically; no drift to report.

---

## 7. Change A applied — sitemap fixed (2026-09-14, approved by Jon)

Applied and verified. `src/app/sitemap.ts` now:

1. `export const dynamic = 'force-dynamic'` — no prerender, so the build cannot freeze it again.
2. A **logged** catch: `console.error('[sitemap] county query failed:', error)`. The route still
   does not 500, which was the original and correct intent.
3. `/leaderboard` and `/new-bookings` added.
4. County URLs emitted for enabled jurisdictions, via the new `src/lib/county-slug.ts`.

Verified:

| Check | Before | After |
|---|---|---|
| Sitemap URLs | 54 | **83** |
| County URLs | 0 | **27** |
| …returning HTTP 200 | — | **27 of 27** |
| Prod vs local sitemap | — | identical (83 / 27) |
| `/leaderboard`, `/new-bookings` in sitemap | absent | present |
| Sitemap query failures logged | (silent) | **0** |
| `/`, `/state/MT`, `/county/MT/flathead`, `/search` | 200 | 200 |

Rollback: `docker tag jailmap-web:rollback-sitemap-20260914-050306 jailmap-web:national-20260907 &&
docker compose up -d --no-deps web`, plus
`cp backups/sitemap.ts.bak-20260914-050306 src/app/sitemap.ts` (the original file was **untracked**
in git, so `git checkout` was never an available rollback).

### The logged catch immediately earned its place

With the silence removed, the very first request surfaced a second, previously invisible defect:

```
[sitemap] county query failed: Error [PrismaClientKnownRequestError]:
Raw query failed. Code: `42501`. Message: `permission denied for table facility_contact_details`
```

`jailmap_app` has full CRUD on `records.inmates` and `records.jurisdictions`, SELECT on the `public`
map tables, and **no grant at all** on `records.facility_contact_details`. This is the same live-DB
grant drift already recorded for `directory_enrichment_queue` and `aggregate_jail_statistics`
(`deploy/init-db.sh` grants on first init; the live DB has since drifted).

The sitemap was adjusted not to depend on that table (see §8), so the fix shipped without a
privilege change. The grant remains an open item:

```sql
GRANT SELECT ON records.facility_contact_details TO jailmap_app;   -- as jailmap_owner
```

---

## 8. What the sitemap now advertises, and the honest caveat

Of the 27 county URLs now in the sitemap, **8 have public booking records and 19 are empty shells**:

```
MT/big-horn  MT/blaine  MT/carbon  MT/deer-lodge  MT/gallatin  MT/granite  MT/madison
MT/meagher   MT/park    MT/phillips MT/pondera    MT/powder-river MT/powell MT/roosevelt
MT/sanders   MT/sheridan MT/stillwater MT/teton    MT/wheatland
```

Those 19 are not a coincidence — they are **exactly** the jurisdictions awaiting remediation
approval: 13 inert (`unverified` + `authorization_reference='pending'` + a county homepage as
`source_url`) + 5 whose county disabled public inmate search (Carbon, Madison, Meagher, Stillwater,
Wheatland) + Gallatin (vendor maintenance).

So the thin-page problem has one real fix, and it is not more code: **approving the remediation
draft** in `2026-09-14-mt-zuercher-remediation.md` collapses the advertised set to actual coverage.
The alternative — a code-level content gate in the sitemap — is a one-line change if you want the
sitemap clean before the remediation is decided.

### Also noted

- `lastModified: new Date()` is recomputed per request, so consecutive sitemap responses differ.
  Harmless, but constant `lastmod` churn makes the hint less useful to crawlers. Worth pinning to a
  real data-freshness timestamp later.
- `compose.override.yaml` hardcodes `jailmap-web:national-20260907` / `jailmap-api:national-20260907`,
  so `RELEASE_TAG` in `.env` is ignored. Every `docker compose build` overwrites the tag the running
  container references. Tag a rollback before each deploy, or that tag is your only history.

---

## 9. Changes A2 and A3 applied (2026-09-14, approved by Jon)

### A3 — grant drift fixed

```
before:  SET ROLE jailmap_app; SELECT count(*) FROM records.facility_contact_details;
         ERROR:  permission denied for table facility_contact_details
applied: GRANT SELECT ON records.facility_contact_details TO jailmap_app;   -- as jailmap_owner
after:   SET ROLE jailmap_app; SELECT count(*) FROM records.facility_contact_details;
         3
```

Grants on the table now read `jailmap_app | SELECT` alongside `jailmap_owner | SELECT,UPDATE,DELETE,
INSERT,REFERENCES,TRIGGER,TRUNCATE`. The grant is DB-level, so it survived the container rebuild that
followed. Rollback: `REVOKE SELECT ON records.facility_contact_details FROM jailmap_app;`

### A2 — content gate applied

The sitemap county query now gates on content rather than the `enabled` flag:

```sql
SELECT DISTINCT j.state, j.county
  FROM records.jurisdictions j
 WHERE j.enabled
   AND EXISTS (SELECT 1 FROM records.inmates i
                WHERE i.jurisdiction_id = j.id AND i.visibility = 'public')
```

The eight counties now advertised are exactly the ones with records:

```
GA/fulton   ID/bonneville   ID/power   MT/flathead
MT/jefferson   MT/missoula   MT/ravalli   MT/yellowstone
```

Verified:

| Check | After A | After A2 |
|---|---|---|
| Sitemap URLs | 83 | **64** |
| County URLs | 27 | **8** |
| …returning 200 | 27/27 | **8/8** |
| Empty shells advertised | 19 | **0** |
| Prod vs local | identical | identical |
| Sitemap query failures logged | 0 | **0** |

The 19 gated-out counties still serve HTTP 200 when visited directly — they are unadvertised, not
broken. They return to the sitemap automatically as their sources are repaired and records land.

Rollback: `jailmap-web:rollback-contentgate-20260914-051014` +
`backups/sitemap.ts.precontentgate-20260914-051014`.

### Deploy hazard confirmed again

`compose.override.yaml` hardcodes the image tags, so `docker compose build` overwrites
`jailmap-web:national-20260907` in place — the tag the running container points at. Rollback images
are the only history. Two are now held:

```
jailmap-web:rollback-sitemap-20260914-050306      ae1832c9af44   (pre-any-fix)
jailmap-web:rollback-contentgate-20260914-051014  78a471715bab   (post-sitemap-fix, pre-gate)
```
