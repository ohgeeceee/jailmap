# JailMap — Month 1 Expansion Plan

Written 2026-09-14. Read `/root/jailmap/MISSION.md` first — its Green/Yellow/Red tiers govern
everything here. Every Red-tier action is drafted into
`agent-queue/jailmap-ops-captain/<date>-<name>/` and waits for Jon's explicit approval.

Goal for the month: **turn JailMap from a 9-jail Montana/Idaho demo into the national reference
surface for jail-custody records, with public-records law (FOIA-class requests) as the primary
acquisition backbone and state/county/jail pages as the SEO engine.**

Two engines, one dependency:

- **Acquisition engine** — public-records requests (state acts, plus federal FOIA where it applies)
  convert "we can't scrape this" into "the agency sends us the file."
- **Distribution engine** — SEO converts coverage into traffic.
- Coverage feeds SEO. SEO without coverage is thin pages; coverage without SEO is a private database.

---

## 1. The honest baseline (measured, not estimated)

### Ingestion and coverage

| Metric | Value |
|---|---|
| Counties in national directory | 3,143 |
| Jails in directory | 3,531 |
| Jails with a real jurisdiction website | 7 |
| Directory rows whose "website" is a Census TIGERweb geometry URL | 3,528 |
| Registered jurisdictions | 51 |
| Enabled for ingestion | 27 |
| **Eligible to run at all** (verified + authorization ref) | **14** |
| Produced a successful run in the last 7 days | 9 |
| Jurisdictions by state | MT 45 registered / 24 enabled / 11 verified-enabled · ID 3 / 2 / 2 · GA 2 / 1 / 1 · SD 1 / 0 / 0 |
| **States with any registered jurisdiction at all** | **4 of 50** |
| Booking records | 4,879 (4,617 public) |
| `states/**/adapter.py` files | 2,978 — **2,947 raise `NotImplementedError`** |
| Real adapters in `backend/adapters/` | 42 files, 11 registered |
| Rows in `data/official-jail-source-leads.csv` | 7 |

**Coverage today: 9 of 3,531 jails actively ingesting — 0.25%.**

### SEO surface (measured against production)

| Metric | Value |
|---|---|
| URLs in the live sitemap | **54** (3 static + 50 state hubs + 1) |
| County URLs in the live sitemap | **0** |
| Distinct enabled counties in the DB | 26 |
| County pages that return 200 | only counties with live data (e.g. `/county/MT/flathead`) |
| County pages that 404 | those without (e.g. `/county/MT/carbon` — source is dead) |
| JSON-LD on a county page | `BreadcrumbList`, `Dataset`, `DataDownload`, `Organization` |
| `/inmate/[booking_id]` | noindexed (correct — keep it that way) |
| `/leaderboard`, `/new-bookings` | return 200, **absent from the sitemap** |

### Two verified defects to fix in Week 1

1. **The sitemap emits zero county URLs while 26 distinct enabled counties exist.** The Prisma
   `$queryRawUnsafe` in `src/app/sitemap.ts` is failing and the `try/catch` — added so the sitemap
   "must not 500 if the schema is briefly unavailable" — silently swallows it. Net effect: the
   exact pages that are supposed to rank are never submitted to Google.
2. **Coverage is claimed, not held.** 27 "enabled" jurisdictions, but 13 are `unverified` +
   `authorization_reference='pending'` with a county *homepage* as their `source_url` and
   `standard_json` as their adapter — structurally incapable of ever running. Coverage reporting
   overstates reality by 13. The remediation draft is already written and awaiting approval.

---

## 2. The FOIA reality check (read before building anything)

**Federal FOIA is 5 U.S.C. § 552. It covers federal agencies only. County jails are not federal
agencies.** A FOIA letter to a county sheriff is the wrong instrument; it will be bounced.

What actually applies, verified:

| Jurisdiction | Instrument | Verified specifics |
|---|---|---|
| Montana | Public Records Act, MCA Title 2, ch. 6 | § 2-6-1006 governs fees and response. The 5-business-day acknowledgment duty runs to "a public agency that is not a local government"; a single, clearly identifiable, readily available record must be produced within 5 working days once acknowledged. **County timing differs — confirm per agency.** |
| Idaho | Public Records Act, Idaho Code Title 74, ch. 1 | § 74-101 definitions, § 74-103 request and response. A request **must clearly state that it is a public records request** or it can be ignored. |
| South Dakota | SDCL ch. 1-27 | § 1-27-1 records open; **§ 1-27-2 records "shall be maintained in its original format or in any searchable and reproducible electronic or other format"**; § 1-27-37 written request to the public record officer. |
| Federal | 5 U.S.C. § 552 (FOIA) | Applies to BOP, USMS, and federal detention/contract data — a **separate, smaller** workstream, not the backbone. |
| Remaining 47 states | one act each | Must be researched and cited individually. **Never write a citation from memory into a request letter.** |

### Five truths that shape the design

1. **A public records act is a right to existing records, not a subscription.** No statute
   obligates an agency to build a report that doesn't exist, or to push you a nightly feed. What
   you can legitimately ask for: *a copy of the record as it is kept, in the electronic format it
   is kept in,* and **separately** a standing/recurring arrangement, which is a negotiation, not a
   statutory entitlement.
2. **"Public" is not the same as "unrestricted reuse."** Republishing arrest data is generally
   lawful where the record is public, but it is not risk-free: keep the correction/dispute path,
   keep the "arrest is not conviction" disclosures visible, and **do not market JailMap for
   employment, tenant, or credit screening** — that drags Fair Credit Reporting Act obligations
   into a project that has no business carrying them.
3. **Expect a 20–40% fulfillment rate on wave one.** Denials, silence, fee quotes, and
   "we don't have it electronically" are the normal outcome, not a failure of the strategy. The
   deliverable is a tracked pipeline and relationships, not a magic data hose.
4. **Vendor portals cut both ways.** Where a county runs Zuercher/Tyler/SmartWEB, the agency often
   cannot hand over a structured extract it does not hold — the vendor does. That makes the vendor
   adapter (Week 1 Day 6) the complement to FOIA, not a competitor of it.
5. **Fees are real.** Most acts permit cost recovery. Always request an estimate before authorizing
   production, and ask for a public-interest fee waiver in the same letter. Never let a request run
   uncapped.

### The lines we do not cross (from MISSION.md, restated)

- No captcha bypass, no login bypass, no paywall circumvention, no `robots.txt` violation. A gated
  source is an **outreach** problem. Record it and move on.
- No third-party aggregator mirror ever treated as an authority. Official county/sheriff/city/
  court/state sources only.
- Adult eligible-custody records only. No juvenile, sealed, expunged, or protected-person records.
- No DOB, residential address, driver license, SSN, or mugshot in public output.
- The $99 name-removal path stays a **human-review fee, never an automatic removal**, and a free
  correction path continues to exist alongside it.
- Per-record pages stay out of the index (privacy + liability at index scale). That decision stands.

---

## 3. The architecture to build

### 3a. Public-records request pipeline (new subsystem)

New tables in the `records` schema — **schema change is Red-tier; draft and approve first.**

```
records.public_records_law
  state, act_name, citation, response_days, acknowledgment_rule, fee_rule,
  format_rule, appeal_body, portal_url, custodian_field, template_id,
  verified_on, verified_by, notes

records.public_records_requests
  id, jurisdiction_id, state, county, agency_name, custodian_name, custodian_email,
  act_cited, template_id, subject_line, body_hash, sent_at, delivery_method,
  first_response_at, estimate_amount, estimate_approved, production_format,
  delivered_at, delivered_files, status, denial_reason, exemption_cited,
  appeal_filed_at, appeal_outcome, recurring, recurrence_interval, next_due_at, notes

records.public_records_events
  request_id, at, actor, event_type, detail   -- full audit trail

records.public_records_corpus
  request_id, received_at, filename, format, sha256, parse_status, parsed_rows,
  staged_rows, notes
```

Status enum: `drafted → sent → acknowledged → estimate_pending → estimate_approved → produced
→ parsed → ingested` and the terminal negatives `denied`, `no_records`, `no_electronic_copy`,
`silent` (no response past the statutory deadline), `withdrawn`.

Design rules:

- Every request cites **one verified statute, one custodian, one specific record class**. No
  fishing expeditions; vague requests are the number-one cause of denial.
- Every request asks for the **native electronic format**, and cites the state's format rule where
  one exists (SDCL 1-27-2 is the model).
- Every request asks for a **fee estimate before production** and a **public-interest fee waiver**.
- Every request requests **recurring production** as a separate paragraph — a negotiation ask, not
  a demand.
- The pipeline is a **loop, not a one-shot**: `silent` past deadline triggers the state's appeal
  body; `denied` with an exemption cite triggers a targeted narrowed re-request.

### 3b. Response intake and normalization

A produced file is just a roster from a different door. Reuse the existing contract:

```
response file (CSV/XLSX/PDF)
  → records.public_records_corpus (hashed, immutable)
  → parser → records.staged_bookings   (staging contract, loose shapes allowed)
  → backend.normalize.normalize()      (INPUT contract: status, booking_number,
                                        first_name, last_name, booking_date,
                                        updated_at, dob, mugshot_url, charges/bonds keyed id)
  → records.inmates                    (public contract: source_updated_at, visibility,
                                        non-null booking_number AND booking_date)
```

Parsers live in `backend/adapters/` alongside the scrapers, named
`foia_<state>_<format>.py`, registered in the same `ADAPTERS` dict, staging-only until review.

### 3c. SEO engine

The strategic insight: **the 3,531-jail directory is indexable content even where no roster
exists.** Every row has a facility name, county, state, and often address, city, zip, phone, and
website. That is a legitimate, content-rich page *today*, and it becomes stronger as ingestion and
records-request status fill in. Coverage no longer gates the SEO surface.

| Page type | Count available today | Index rule |
|---|---|---|
| State hubs `/state/[abbrev]` | 50 (already live) | index |
| County pages `/county/[ST]/[county]` | **3,143** — not 26 | index when the county has ≥1 facility row |
| Jail/facility pages `/jail/[state]/[county]/[slug]` | **3,531** — does not exist yet | index when the facility row has real metadata |
| Records-request/transparency pages | 1 per county (3,143) | index — unique, useful, high-trust, natural links |
| Guides (`/guides/[state]`) | 50 + topical | index |
| `/leaderboard` | 1 | index (content-rich) |
| `/new-bookings` | 1 | index (feed, keep thin) |
| `/inmate/[booking_id]`, `/search` | many | **noindex, permanently** |

Structural data to add, in priority order:

1. `WebSite` + `SearchAction` on `/` — earns the sitelinks searchbox.
2. `GovernmentOrganization` / `LocalBusiness` on jail pages, with address, phone, geo.
3. `FAQPage` on state guides and records-request pages (real Q&A only — no invented questions).
4. `ItemList` on state pages enumerating that state's counties/facilities.
5. `Dataset` with a `distribution` array on records-request pages (Google rejects `Dataset`
   without `distribution` — the county page already gets this right; replicate it).
6. `BreadcrumbList` everywhere (already on county pages).

Non-negotiable page-level requirements for anything indexable: unique `generateMetadata`
title/description, `alternates.canonical`, a visible "data is sourced from official records,
arrest is not conviction" disclosure, a correction/removal link, and a last-updated timestamp.
Thin pages with no distinct data stay `noindex` until they have content.

---

## 4. The month

Each day has one objective, prompts for the agent, scripts, and a hard exit criterion.
**Do not roll into the next day with the previous day's exit criterion unmet** — that is exactly
how the 2,947-stub illusion got built.

### Week 1 — Truth, law, and the index

**Day 1 — See the truth; kill the false numbers.**
- Re-run the coverage audit; confirm the 9-jail number from live data.
- Approve and apply the pending remediation draft
  (`agent-queue/jailmap-ops-captain/2026-09-14-mt-zuercher-remediation.md`): disable the 5
  county-disabled sources, disable the 13 inert ones, add vendor-maintenance classification,
  drop `verify=False` in `mt_zuercher.py`.
- Fix the sitemap defect: find the real exception, stop swallowing it, and confirm county URLs
  appear. Do not ship the `try/catch` as a silent failure again — log it.
- *Exit:* `docs/coverage-baseline.md` shows a number you trust, that number is *lower* than before,
  and `curl -s https://jailmap.com/sitemap.xml | grep -c county/` is greater than 0.

**Day 2 — The public-records law matrix.**
- Research and record `records.public_records_law` rows for the first 10 states: act name,
  citation, response/acknowledgment days, fee rule, format rule, appeal body, custodian title,
  online portal if one exists — **each verified against the state legislature's own site**, with
  `verified_on` and the source URL. Never from memory.
- Start with MT, ID, SD (already verified above), then GA, TX, FL, CA, AZ, CO, WA.
- *Exit:* 10 rows, every one carrying a primary-source URL. Any state you cannot verify stays
  blank rather than guessed.

### Day 3 — SEO foundation, part 1: make the pages exist.

> **REVISED 2026-09-14 — see `docs/day1-findings.md` §3–5.** The original version of this day assumed
> the 3,531-jail directory was indexable content. It is not: address is populated on 7 rows, phone on
> 3, and `records.facility_contact_details` has 3 rows against a 3,143-row enrichment queue. Worse,
> `public."Jail"` (`census-landmark-<OID>` keys) and `records.jurisdictions` (UUIDs keyed by
> state+county) **do not join at all** — a name-based match finds 3 of 3,531. Facility pages built
> before that bridge exists would be 3,531 thin pages. Revised order in
> `agent-queue/jailmap-ops-captain/2026-09-14-index-and-facility-prep/`: (A) fix the sitemap,
> (B) build the facility↔jurisdiction bridge, (C) enrich, then publish.

- Fix the sitemap: stop prerendering it, log the failure instead of swallowing it, add
  `/leaderboard` and `/new-bookings`, and emit the **29** content-eligible counties (up from 0).
  Root cause of the current defect: `docker build` has no `DATABASE_URL`, `src/lib/prisma.ts` throws,
  and `sitemap.ts`'s bare `catch` froze a 54-URL sitemap into the image.
- Build the facility↔jurisdiction bridge and the shared county-slug normalizer
  (directory says `"Flathead County"`, jurisdictions say `"Flathead"` — every unnormalized join
  fails silently).
- Work `records.directory_enrichment_queue` for a first tranche of 25–50 counties, and extract the
  **records custodian name and email** from the same pages — that is the FOIA pipeline's input.
- Gate every new page on content. Facility pages ship only where `facility_contact_details.verified_at`
  is set; never from raw directory rows.
- *Exit:* `curl -s https://jailmap.com/sitemap.xml | grep -c 'county/'` equals the count of
  content-eligible counties; the bridge exists with 3 automatic matches and a visible unmatched
  remainder; enrichment has run for ≥25 counties with `verified_at` set.

**Day 4 — SEO foundation, part 2: make them rankable.**
- Add the structured-data set from §3c to the new page types.
- Add `/guides/[state]` for the 10 states in the law matrix: "How to request jail records in
  [State]" — statutory citation, custodian, deadline, fees, appeal path, plus an FAQPage. This
  doubles as the outreach artifact for Week 2.
- Verify: Search Console + Bing Webmaster verified, sitemap submitted, `/`, `/state/MT`,
  `/state/ID`, `/state/GA` requested for indexing.
- *Exit:* JSON-LD validates in Google's Rich Results test on one page of each type; Search Console
  shows the sitemap accepted with a URL count above 500.

**Day 5 — FOIA wave 1: 50 requests out.**
- Draft the request template per state from the law matrix. Required paragraphs: identity, exact
  record class, native electronic format (citing the state's format rule), fee estimate requested
  before production, public-interest fee waiver, recurring-production ask, and a request that any
  denial be issued in writing with the exemption cited.
- Select the 50 targets by expected value: states with the most counties, counties with a real
  sheriff site and **no** vendor portal, plus the 5 MT counties whose public roster just went dark
  (Carbon, Madison, Meagher, Stillwater, Wheatland) — a records request is the correct response to
  a portal being disabled, and it is the one thing the MT remediation draft cannot do.
- Load all 50 into `records.public_records_requests` as `drafted`.
- **Sending is Red-tier.** Draft, review, approve, then send.
- *Exit:* 50 requests drafted and tracked with a verified citation each; the send list is approved
  and the send is executed.

**Day 6 — The complement to FOIA: one vendor family, built properly.**
- Build the top vendor-family adapter from the census (Zuercher is the proven one: a plain JSON
  POST API at `/api/portal/inmates/load`, already working for Ravalli). Parameterize it by tenant.
- Register the orphaned working adapters in `backend/adapters/` (42 files, 11 registered) — cheap
  coverage with no new code.
- Adapters emit the **public** contract from the start (`source_updated_at`, `status`, non-null
  `booking_number`/`booking_date`, charges/bonds keyed `source_id`) — retrofitting costs
  round-trips.
- *Exit:* one vendor family ingests staging-only from ≥10 jurisdictions in a dry run with zero
  unhandled exceptions; every orphaned adapter is registered or deleted.

**Day 7 — Close the loop and set Week 2.**
- Publish the FOIA request dashboard as a public transparency page (`/records-requests`): by state,
  requests sent, produced, denied, silent. This is honest, unique, and linkable.
- *Exit:* Week-1 review written — coverage start vs. end, indexable URL count start vs. end,
  requests sent, and the single biggest remaining blocker named.

---

### Week 2 — Scale acquisition to ~300 requests and the full national census

**Day 8–9 — Complete the national source census.** Full pass over the 2,648 resolving `.gov`
candidates with `--concurrency 12` and resume. Politeness invariants hold: `robots.txt` per origin,
1 req/sec/host, 12s timeout, 400 KB cap, gated sources recorded and abandoned.
*Exit:* `data/national/source-census.csv` covers ≥2,000 domains with access classes assigned.

**Day 10–11 — FOIA wave 2: 250 more requests.** Prioritized by the census: counties classified
`captcha_gated`, `login_required`, `blocked`, or `robots_disallowed` are *exactly* the ones that
will not yield to engineering and *will* yield to a letter. Add the `no_roster_found` set as the
second tranche. Standing/recurring production is the ask on every one.
*Exit:* 300 requests tracked; ≥25 with a first response.

**Day 12 — Response intake pipeline, built and tested.** Parsers for the formats agencies actually
send: CSV, XLSX, and PDF. Fixture-backed tests (one per format per state), staging rows produced,
nothing auto-published.
*Exit:* a real produced file from wave 1 runs end-to-end to `records.staged_bookings` and the parse
is reproducible from the stored fixture.

**Day 13 — Vendor families 2 and 4.** Build the second-largest family from the census histogram and
register it. If the histogram is still bespoke-dominated (`search_form` + `html_roster` ≈ 48% on
the first pass), build the *generic* `search_form` adapter with a per-county config block instead —
one adapter, many counties, small configs.
*Exit:* two or more vendor/config families covering ≥50 jurisdictions in dry runs.

**Day 14 — Review.** Requests sent / produced / denied / silent; new jails ingesting; new indexable
pages. Name the bottleneck.

---

### Week 3 — Ingest at scale, and make the index earn

**Day 15–17 — Volume ingestion + the records-request corpus.** Every produced file becomes live
data: parse → normalize → stage → review → enable. Each enablement is Red-tier and individually
approved. Target: 100–200 jails ingesting, up from 9.
*Exit:* `records.ingestion_runs` shows >100 jurisdictions with a success in the last 7 days.

**Day 18–19 — Programmatic SEO at directory scale.** Generate county pages for every county that
has a facility row (3,143 potential), populated with: facilities, jail contact info, live roster
status, last-updated timestamp, records-request status and history, how-to-request guide, and the
correction path. Internal-link each county page from its state hub and each facility page from its
county page. **Gate on content**: a county with no facility metadata and no live source stays
noindexed rather than shipping an empty page.
*Exit:* ≥1,500 indexable county pages live, every one with distinct content, canonical, and JSON-LD.

**Day 20–21 — Automate the loop.** systemd timers for: ingestion across enabled jurisdictions,
source-health probe, coverage census refresh, records-request deadline watch (auto-flags `silent`
past the statutory deadline and queues the appeal), and a 07:00 MT digest. Escalate only on the
MISSION.md real-time triggers. Draft every unit; enabling them is Red-tier.
*Exit:* the loop runs unattended 24h; digest is one screen with a real number at the top.

**Day 22 — Measure the index.** Search Console: indexed pages, impressions, clicks, top queries.
Rank the new pages against "how to request [county] jail records", "[county] jail roster",
"[state] inmate search". Kill any page type with zero impressions after two weeks of indexation.
*Exit:* a ranked list of page types by impressions, and a decision on which to mass-produce.

---

### Week 4 — Consolidate, measure, decide

**Day 23–25 — Fill the gaps the numbers expose.** Whatever the Week-3 metrics say: more law-matrix
states, more vendor families, more requests to the counties that showed the highest yield, or more
of the page type that actually earns impressions. This week is deliberately unscheduled until the
data lands — scheduling it now would be guessing.

**Day 26 — The FOIA second half.** Send wave 3 to every jurisdiction that went `silent` (with the
state appeal body cited) and every `denied` county with a narrowed, specific re-request.

**Day 27 — Hardening.** `robots.txt`/`sitemap.xml` audit, canonical audit for duplicate county
slugs, Core Web Vitals, JSON-LD validation sweep, correction-path end-to-end test (does a real
removal request actually get processed?), and a privacy regression test that no public endpoint
leaks DOB or mugshot.

**Day 28–29 — Month-1 review.**
- Coverage: jails ingesting start → end; states with any registered jurisdiction start → end.
- Requests: sent, acknowledged, produced, denied, silent; cost per new jurisdiction (review minutes
  vs. machine time vs. fees).
- SEO: indexable URLs, indexed pages, impressions, clicks; top-10 queries.
- Then set Month 2 against whichever of the three leverage tiers (vendor adapters, discovery, review
  throughput) is now binding.

**Day 30 — Decision gate.** Month 2 continues, or the strategy changes, on evidence:

| Metric | Baseline (2026-09-14) | Month-1 target |
|---|---|---|
| Jails ingesting (7d success) | 9 | 100–200 |
| States with any registered jurisdiction | 4 | 15–25 |
| Public-records requests sent | 0 | 300–400 |
| …produced / denied / silent | — | 60–120 / tracked / tracked |
| Indexable URLs | 54 | 5,000+ |
| …county pages indexed | 0 | 1,500+ |
| Sitemap county URLs | 0 | >1,500 |
| GSC impressions (30d) | unknown | first real curve |

---

## 5. Red-tier items needing approval

Already drafted and waiting:

- `agent-queue/jailmap-ops-captain/2026-09-14-mt-zuercher-remediation.md` — adapter maintenance-mode
  classification, disable 5 dead sources, disable 13 inert sources, remove `verify=False`.

This plan will require, in order:

1. **Schema migration** — the four `records.public_records_*` tables. Reversible; `ALTER`/`CREATE`
   only, no destructive change.
2. **Sitemap fix + facility page build** — application code in `/root/jailmap/`, then
   `docker compose build api web && up -d`. Rollback tags exist from the 2026-09-14 deploy.
3. **Outbound email** — every records request. Drafted, tracked, presented as a batch for approval,
   sent only on explicit go.
4. **Source enablement** — each jurisdiction, individually, after review. Never as a batch.
5. **systemd timers** — drafted, not enabled, until the digest channel exists.

---

## 6. What this plan deliberately does not do

- **Does not promise 3,531 working scrapers.** The honest month-one goal is hundreds of sources
  classified, a handful of vendor families built, and a request pipeline that keeps producing for
  years.
- **Does not treat the 2,947 stub `adapter.py` files as progress.** They are scaffolding. The
  number that matters is jurisdictions with a successful run in the last 7 days.
- **Does not bypass captcha, login, paywalls, or `robots.txt`.** Gated sources become letters, not
  workarounds.
- **Does not use third-party aggregator mirrors as authority.** They are competitors, not sources.
- **Does not index per-record pages.** Ever. That is the line between a public-records mirror and a
  defamation and privacy liability.
- **Does not market JailMap for employment, tenant, or credit screening.** FCRA territory, and not
  this project.
- **Does not turn the paid removal path into a removal.** Payment buys human review; the record
  comes down only through review, and the free correction path stays open.
- **Does not count a request as a source.** A sent letter is a pipeline event, not coverage.
