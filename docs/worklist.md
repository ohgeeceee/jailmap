# JailMap — Master Worklist

Created 2026-09-14. Working list, top to bottom. Status updated as items complete.

**Standing constraint:** I will not enable a jurisdiction (`enabled=true`) or set
`staging_only=false`. Publishing a private individual's booking record is the one irreversible
action in `MISSION.md` — a wrong publish cannot be recalled. Everything else on this list gets
executed without waiting. Adapters are built and tested **staging-only**; a human flips the switch.

---

## Tier 0 — Correctness and trust

- [ ] 0.1 Page titles: stray 🐴 emoji and duplicated `| JailMap | JailMap` in `<title>`
- [ ] 0.2 Audit `robots.ts` / `sitemap.ts` — canonical hosts, noindex coverage, enabled counties
- [ ] 0.3 Verify admin panel end-to-end (coverage/ingestion/pipeline/revenue tabs, auth gate)
- [ ] 0.4 Structured data (JSON-LD) present and valid on indexable pages
- [ ] 0.5 Canonical URL + `metadataBase` correctness across public pages
- [ ] 0.6 Confirm no restricted field (DOB, mugshot) leaks in any public response

## Tier 1 — Ingestion (the actual mission)

- [x] 1.1 Generic HTML-roster table parser — **BUILT** (`backend/adapters/html_roster.py`,
      registered as `html_roster_staging`, 11 unit tests passing). Uses stdlib `html.parser`
      (container has no bs4/lxml). Requires an identity column, never invents custody status,
      staging-only so imperfect rows are flagged not published.
      **Corrected target count: 5, not 72.** The old census labelled any page that *mentioned*
      "inmate" as `html_roster`; five sampled targets contained zero `<table>` elements. With the
      classifier fixed (reusing this parser's column mapping) the true homepage-depth count across
      2,648 domains is **5**. The parser is still the right tool — it is the *classifier* that was
      lying, and the same code now classifies correctly.
- [x] 1.2 Socrata open-data adapter — **BUILT** (`backend/adapters/socrata.py`, registered as
      `socrata_staging`, 9 unit tests passing). Includes `discover(domain)` against the Socrata
      catalog API for scouting, paginated SoQL fetch, bounded at 20 pages / 20k rows. 7 portals
      identified; dataset IDs still need discovery before ingest.
- [x] 1.3 Two-hop sheriff-link crawler — **BUILT** (`scripts/national/crawl_sheriff_links.py`,
      `backend/tests/test_crawl_sheriff_links.py`, 17 tests passing). Bounded depth 2, per-hop
      robots checks, 1 req/sec/host, cross-domain link following, resumes interrupted runs.
      Outputs source-lead CSV in `import_source_leads.py` format for direct handoff.
- [x] 1.4 Audit `backend/adapters/` — **do NOT register blindly.** 42 modules, 36 orphaned. Of the
      orphans: **21 require Playwright** (not in the container's requirements — they crash on run),
      **18 hardcode `booking_number: None`** (schema requires NOT NULL — inserts fail). Zero are
      stubs; they are broken, not empty. Only 9 orphans have no obvious blocker and each needs a
      live dry-run before it can be trusted. Registering them as-is would publish garbage person
      records. Individual verification is now a per-adapter task, not a bulk flip.
- [ ] 1.5 MT Zuercher remediation (maintenance-mode detection, disable dead sources, drop `verify=False`)
- [ ] 1.6 Staging-only dry-run proving the new adapters against live sources
- [ ] 1.7 Ingest error classification so vendor maintenance ≠ parse failure in the health panel

## Tier 2 — Coverage and discovery surface

- [ ] 2.1 County pages render for every enabled jurisdiction; 404 (not 500) when none
- [ ] 2.2 State pages list counties with live data and link each county page
- [ ] 2.3 Sitemap covers all enabled counties and states
- [ ] 2.4 Public coverage/sources page showing real, current coverage numbers
- [ ] 2.5 Search: verify Meilisearch outbox drains and index stays fresh

## Tier 3 — Operations (make it run without me)

- [ ] 3.1 systemd timer/service for the daily ingest loop
- [ ] 3.2 Health watchdog with `MISSION.md` escalation triggers only
- [ ] 3.3 Failure triage report (ranked fix list, not a log wall)
- [ ] 3.4 Backups verified restorable, not just present
- [ ] 3.5 `docs/AGENTS.md` in this repo contains Montana Blotter content — replace

---

## Execution log

- 2026-09-14: **1.3 BUILT** — two-hop sheriff crawler (`scripts/national/crawl_sheriff_links.py`).
  Bounded depth 2, per-hop robots, 1 req/sec/host, cross-domain link following, resume. 17 tests
  passing. Outputs source-lead CSV for direct handoff to import_source_leads.py.

- 2026-09-14: Confirmed name-removal checkout works live (form → POST 200 → Stripe redirect, verified
  in a real browser). The reported failure was the old `status_code=303` bug, already fixed.
- 2026-09-14: Found 0.1 via that test.
- 2026-09-14: **0.1 DONE** — 14 page titles fixed across 13 files (`%s | JailMap` template was
  double-appending the brand). Deployed, verified live.
- 2026-09-14: **0.2 DONE** — sitemap was advertising `/leaderboard` and `/new-bookings`, both of
  which set `index: false`. Removed; 64 → 62 URLs. robots.txt was already correct.
- 2026-09-14: **1.1 DONE** — generic HTML roster parser built, 11 tests.
- 2026-09-14: **1.2 DONE** — Socrata adapter built, 9 tests.
- 2026-09-14: **1.4 DONE** — adapter audit. 21/42 need Playwright, 18 set `booking_number: None`.
  Do not bulk-register.
- 2026-09-14: **Found and fixed a lying classifier.** `html_roster` was assigned on keyword
  presence; five sampled targets had zero tables. Fixed to require a real identity-column table,
  reusing the new parser. True homepage-depth count: **5 of 2,648**, not 72. All docs and the
  worklist corrected.
- 2026-09-14: Deployed api + web. 13 adapters registered (was 11). Site 200 across the board,
  admin gate returns 401 for anonymous. Rollback tags: `rollback-20260914-053047`.
- 2026-09-14: **2.1/2.2 verified** — county pages 200, state pages 200, no-record county 404s
  (content gate working), county content gate matches the 8 jurisdictions with live records.

## Next up

`search_form` (193) needs structural verification before it can be called a roster search — it has
the same over-reporting risk `html_roster` had. After that, per-source adapter work and outreach
on the discovered leads.
