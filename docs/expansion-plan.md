# JailMap — Path to #1

Written 2026-09-14. Read `MISSION.md` first: its Green/Yellow/Red tiers govern every item here.
This sheet does **not** replace `month-1-expansion-plan.md` (FOIA acquisition + SEO) or
`national-rollout-plan.md` (Week-1 coverage) or `census-findings.md` (vendor census). It
reconciles them into one sequence and adds the two layers neither covers: **the public API
product** and **the operating team that actually runs**.

Every number below is measured, not estimated, and cites where it came from.

---

## 1. What "#1" means, so it can be measured

"Number one" is worthless as an ambition and useful as a metric. Three claims, three numbers:

| Claim | Metric | Where we are | Bar to hold the claim |
|---|---|---|---|
| Most complete national roster coverage | Jails ingesting successfully in 7 days | **9 of 3,531 (0.25%)** | 1,000+ (Jail Data Initiative already collects >1,000 public rosters) |
| Freshest custody data | Median hours since last successful run, per enabled source | **19 of 27 enabled never succeeded once** | median < 6h on 95%+ of enabled sources |
| Most useful public API | Published, documented, metered endpoints | **0 (an `ApiKey` model exists with no metering)** | 6+ endpoints, free tier for press/research, webhooks |

Competitive floor, from public sources: JailBase sells arrest/mugshot data via RapidAPI;
offendersearch.app charges $0.15/call for county+state lookups; TNDocket sells state-level
commercial API access; Vera publishes county jail *aggregates* 1970–2026; NYU's Jail Data
Initiative collects individual-level records from >1,000 public rosters; countyjailroster.net
claims 100+ counties standardized. Academics own the aggregate story. Nobody owns
**fresh, provenance-carrying, individually-attributable custody data with a usable API**.
That is the open lane, and it is winnable.

---

## 2. The honest baseline (measured)

| Metric | Value | Source |
|---|---|---|
| Counties / jails in directory | 3,143 / 3,531 | `docs/coverage-baseline.md` |
| Jails with a real jurisdiction website | **7** | same |
| Registered jurisdictions | 51 | same |
| Enabled | 27 | same |
| Eligible to run at all (verified + authorization ref) | **14** | month-1 §1 |
| Ingesting successfully in last 7 days | **9** | same |
| Enabled but never succeeded | **19** | `/api/admin/freshness`, 2026-09-14 |
| Ingestion runs: failed of total | **411 of 516** | `records.ingestion_runs` |
| `states/**/adapter.py` files | 2,978 | month-1 §1 |
| …that raise `NotImplementedError` | **2,947 (99.0%)** | same |
| Real adapters in `backend/adapters/` | 42 files, **11 registered** | same |
| Rows in `data/official-jail-source-leads.csv` | **7** | same |
| County URLs in the live sitemap | **0** | month-1 §1 |
| CI workflows | **none** (`.github/workflows` absent) | filesystem, 2026-09-14 |

Two structural facts that shape everything:

1. **The 2,978 adapter files are scaffolding, not coverage.** Any dashboard reporting them as
   progress is lying to its operator. Day 1 of any plan is deleting that illusion.
2. **"Enabled" currently overstates coverage by 13.** Those 13 have a county *homepage* as
   `source_url` and `standard_json` as adapter: structurally incapable of returning a roster.

---

## 3. Sequence

Ordered by dependency, not by ambition. Each stage has an exit criterion; do not start the next
until it is met.

### Stage 0 — Stop lying to ourselves (all Red, all already drafted)

| # | Item | Why first | Exit criterion |
|---|---|---|---|
| 0.1 | Land `2026-09-14-mt-zuercher-remediation.md`: disable 5 dead + 13 inert sources, remove `verify=False` | Coverage claims must equal reality before anything is built on them | `/api/admin/freshness` shows enabled == capable |
| 0.2 | Fix the sitemap defect (`src/app/sitemap.ts` swallows a failing `$queryRawUnsafe`) | The pages meant to rank are never submitted | sitemap returns >0 county URLs, and the failure is loud not silent |
| 0.3 | Add CI (`.github/workflows`): `pytest backend/tests/`, `node --test`, `tsc` | No gate exists; every later claim is unverifiable without it | a PR that breaks a test fails CI |

### Stage 1 — Make the 27 work before making 2,700 more

Reliability precedes scale; at 80% run failure, adding sources multiplies breakage.
Kill criteria are explicit: a source that cannot succeed after N attempts is disabled, not carried.

Exit: 20+ enabled sources with a 24h-fresh successful run; failure rate < 20%.
Uses: `records.ingestion_runs.error_detail` (shipped 2026-09-14), `/admin?tab=ingestion`.

### Stage 2 — Trustworthy census (the decision input for adapters)

`census-findings.md` says plainly: 132 jails classified, sample 69% FL+ID, vendor thesis weak at
county tier (47.7% bespoke), "do not commit to a vendor adapter yet on this evidence."
CISA `.gov` registry maps 2,089 of 3,143 counties to an official domain, incl. 267 sheriff domains.

Exit: vendor/method histogram over a nationally distributed sample, with a written
recommendation on which adapter family to build first — signed off before code is written.

### Stage 3 — Adapter families, config-driven

Where the volume is, per the census: **generic HTML roster + search-form** first, then vendor
families (Zuercher, SmartWeb, Socrata open data, Tyler Odyssey…). A new county must be a *config
row + a test fixture*, never a new Python module. Register the ~29 orphaned real adapters
(`scripts/national/audit_adapters.py --unregistered`) — cheap coverage, no new code.

Exit: one new county onboarded end-to-end in < 30 minutes of operator time.

### Stage 4 — The API product (see §4)

Exit: 6 endpoints live, metered, documented; one external consumer (press, researcher, or
nonprofit) using it in production.

### Stage 5 — Consumer value

Alerts (new booking / release at a chosen jail), custody history, county pages with real history.

### Stage 6 — Trust as the moat

Free corrections (shipped), published retention, provenance on every record, public freshness
SLA page, bulk open data. A competitor whose business model is paid removal *cannot* copy this.

---

## 4. The API product — what nobody else offers

Ordered by value ÷ effort. Each names its data dependency, and whether that dependency already
exists in the schema.

| # | Endpoint / feature | What it does | Data dependency | Status |
|---|---|---|---|---|
| 1 | **Coverage & freshness API** `GET /api/v1/coverage`, `/coverage/{state}`, `/sources/{state}/{county}` | Publishes which counties we cover, last success, expected cadence, source URL, adapter family | `records.jurisdictions` + `records.ingestion_runs` | **data exists** (built for the admin panel) |
| 2 | **Record provenance** — fields on every record | `source_url`, `fetched_at`, `snapshot_id` on each booking so any record is traceable to the official page and minute | needs columns on the records schema | small migration |
| 3 | **Change webhooks** `POST /api/v1/subscriptions` → `new_booking`, `released`, `charge_amended` | Push, HMAC-signed, retried. Polling is what everyone else makes you do | needs an events table + dispatcher | new subsystem |
| 4 | **Custody history** `GET /api/v1/custody/{state}/{county}/{booking_number}/history` | Status transitions with timestamps instead of a one-shot snapshot | `Roster.scrapeDate` history + booking keys today; a status-transition table for clean history | partially exists |
| 5 | **Geospatial** `GET /api/v1/jails?lat=&lng=&radius_km=` and `/jurisdictions/resolve` | "Which jail holds someone arrested at this address" | `Jail.latitude/longitude` | **schema exists** |
| 6 | **Bulk daily snapshots** `GET /api/v1/snapshots/{date}/{state}.csv.gz` + manifest (rows, checksum) | Research-grade open data; competes with Vera/JDI on freshness | nightly export job | new job |
| 7 | **Charge & bond intelligence** | Normalized offense categories (statute → class), bond distribution per county | `Roster.charges[]`, `Roster.bondAmount` | data exists, normalization does not |
| 8 | **Key metering + self-serve** | Usage counters, quotas, tiers, 429s, key rotation | `ApiKey` exists with only `lastUsed` | needs counters/quotas |
| 9 | **Embeds** | County roster widget (iframe + JSON) for press and county sites | public records API | thin layer over #1/#6 |

Free tier for press, researchers and nonprofits is deliberate: it is how the coverage claim gets
cited, and citations are cheaper than ads.

---

## 5. The team

`hermes/jailmap-bots.yaml` defines seven bots and four lanes. **Status: designed, not started.**
Only `jailmap-ops-captain` has an `agent-queue/` directory and a cron entry; the other six have
never run. Starting them is the single highest-leverage operational act available.

| Bot | Mandate (Green = may do alone) | Cadence | Writes only to |
|---|---|---|---|
| `jailmap-ops-captain` | triage, route, require review before Red | daily 07:00 MT digest | `agent-queue/jailmap-ops-captain/` |
| `source-scout-{west,south,north}` | find official sources, write **disabled** leads | daily per region | `data/official-jail-source-leads.csv`, `docs/source-discovery-log.md` |
| `feed-builder` | audit orphaned adapters, draft registrations + staging-only adapters | daily | `agent-queue/feed-builder/` (drafts) |
| `privacy-reviewer` | verdicts on every lead/source: READY_FOR_ADAPTER / BLOCKED / NEEDS_REVIEW | on new leads | `agent-queue/privacy-reviewer/` |
| `search-indexer` | Meilisearch + outbox lag + hydration health | daily | `agent-queue/search-indexer/` |
| `site-operator` | service health, backups, TLS, deploy runbook | daily (exists) | `agent-queue/site-operator/` |

Discipline that makes the team safe to run unattended: Green bots may read anything and write only
drafts; nothing enables a source, publishes a record, sends external email, or touches production
timers without Jon. Cadence is cron, output is a digest to the bot's own queue directory, and
silence is treated as failure — a bot that produces nothing is broken, not idle.

---

## 6. Legal and ethical guardrails (not optional garnish)

- **Never sell or expose the data for employment, housing, credit or tenant screening.** That
  converts JailMap into a consumer reporting agency under the FCRA with accuracy and dispute
  obligations it cannot meet. Any commercial API tier needs a contractual purpose restriction.
- **No paid removal tied to publication.** The mugshot-site category (Mugshots.com and its
  unpublish scheme) was prosecuted, and the whole category is discredited. Corrections stay free
  and fast; the $99 removal is a *review* fee on a queue a human works, never a delete-on-payment.
- **Publish the retention rule** and honour it mechanically, so "we keep it forever" is never the
  implicit answer.
- **Provenance on every record** so the public, journalists and defence counsel can always reach
  the official source and see how fresh it is.

---

## 7. The numbers to watch weekly

| Metric | Now | 90-day target |
|---|---|---|
| Jails ingesting successfully (7d) | 9 | 400 |
| Enabled and *capable* sources | 14 | 400 |
| Median freshness (hours since success) | never (19 of 27) | < 6 |
| Ingestion failure rate | 80% | < 15% |
| States with any registered jurisdiction | 4 | 25 |
| County pages indexed | 0 | 1,000 |
| Public API endpoints live | 0 | 6 |
| External API consumers | 0 | 5 |
| Median correction turnaround | untracked | < 48h |

---

## 8. Deliberately not doing (considered and deferred)

- **Not** writing 3,531 bespoke scrapers, and not counting the 2,978 scaffolding files as progress.
- **Not** committing to a vendor-family adapter before the CISA-distributed census is in.
- **Not** scraping around captcha, login, paywall, robots or rate limits, on any source, ever.
- **Not** identity resolution across jurisdictions: booking records are not a person registry, and
  a false merge would accuse an innocent namesake. History stays keyed to booking identity.
- **Not** selling screening-grade data (see §6).
- **Not** enabling sources in batches: one jurisdiction, one review, one approval.

---

## 9. What I could not verify

- Whether `scripts/national/audit_adapters.py` and `vendor_dryrun.py` exist and run as the
  rollout plan's Day-3 section assumes (it presents them as commands; I have not executed them).
- The real count of *working* orphaned adapters (the plans say 29; only a run of that audit
  confirms it).
- Whether any external consumer currently uses the public API, or whether `ApiKey` rows exist.
- Live search visibility (GSC impressions) — the 54-URL sitemap figure is from the plan, not a
  live fetch.
