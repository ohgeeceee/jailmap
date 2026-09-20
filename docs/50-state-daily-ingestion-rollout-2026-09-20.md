# 50-State Daily Ingestion Rollout

Date: 2026-09-20
Owner: JailMap operations
Scope: planning and staging work only. No source is enabled, published, scheduled, or promoted by this document.

## Goal

Get at least one official jail/correctional custody source from every U.S. state ingesting daily into JailMap, with public publication only after source review, adapter validation, privacy review, and owner approval.

## Current State

Measured from production Postgres on 2026-09-20:

| Metric | Count |
|---|---:|
| States in public directory | 50 |
| Counties in public directory | 3,143 |
| Jails in public directory | 3,531 |
| States with production-enabled ingestion success in last 7 days | 11 |
| States with staging-only ingestion success in last 7 days | 29 |
| States with no successful source yet | 10 |
| Production-enabled jurisdictions | 27 |
| Production-enabled jurisdictions with success in last 7 days | 26 |
| Current inmate rows | 7,498 |
| Public-visible inmate rows | 6,481 |
| Adapter staging rows | 621 |

The public directory scaffold exists for all states and jails. The unfinished work is verified official roster coverage, adapter hardening, review, and daily scheduling.

## State Coverage Buckets

### Production coverage exists

These states already have at least one production-enabled source with a successful run in the last 7 days:

CA, FL, GA, ID, MT, NC, NY, OH, TN, TX, WY

Immediate next work:

- Fix enabled-source failures: Franklin ID `ConnectTimeout`, Cassia ID `UniqueViolation`, Fulton GA `ValueError`.
- Review zero-record successes so empty jails are not masking parser/source failures.
- Confirm each source has an expected daily cadence and stale-source alert.

### Staging coverage exists

These states have staging-only successful runs and need promotion review, not first-source discovery:

AL, AR, AZ, CO, DE, HI, IA, IL, IN, KS, KY, MA, ME, MI, MN, MO, MS, ND, NE, NH, NJ, NM, OR, PA, SD, UT, VA, WA, WV

Promotion checklist for each state:

1. Confirm source is official and public.
2. Confirm terms/robots/access do not prohibit automated retrieval.
3. Confirm adult custody only or reliable juvenile/protected-person exclusion.
4. Confirm no DOB, address, SSN, DL, or mugshot publication without separate review.
5. Run adapter dry-run and compare row count against source UI.
6. Stage records only.
7. Owner approves production `enabled=true`, `staging_only=false`, and daily schedule.

### Missing first successful source

These states need first-source discovery or adapter work:

| State | First candidate | Source URL | Type | Notes |
|---|---|---|---|---|
| AK | Alaska DOC offender/inmate search | https://www.doc.alaska.gov/ | state DOC search | Official statewide DOC site; verify whether current jail/pretrial custody is searchable before adapter work. |
| CT | Connecticut DOC Inmate Search | https://portal.ct.gov/DOC/Services/Inmate-Search | state DOC search | Official CT DOC search; CT has unified state correctional system context. |
| LA | LA VINE / Orleans roster family | https://lcle.la.gov/programs/lavine/lavine_rosters/ | vendor roster family | Official LCLE page documents parish roster URLs such as Orleans.LAVINE.org; high-leverage adapter family. |
| MD | Maryland DPSCS Incarcerated Individual Locator | https://dpscs.maryland.gov/services/ii-locator.shtml | state locator | Official DPSCS locator; likely JS/search flow. |
| NV | Clark County Detention Center inmate search | https://www.clarkcountynv.gov/government/departments/detention_center/inmate-search | county search | Official Clark County route points to current in-custody search. |
| OK | Payne County Sheriff's Office inmate search | https://paynecountyok.gov/inmate-search | county search | Existing local probe says likely JS-rendered; use Playwright/staging first. |
| RI | Rhode Island DOC incarceration search | https://doc.ri.gov/family-visitors/incarceration-search | state DOC search | Official RIDOC incarceration search with disclaimer gate. |
| SC | Greenville County Detention Center inmate search | https://www.greenvillecounty.org/disclaimer/InmateSearch.aspx | county search | Official county detention center search with terms gate. |
| VT | Vermont offender locator | https://www.vermont.gov/service/offender-locator | state DOC locator | Official Vermont.gov service points to public roster URL. |
| WI | Dane County Sheriff current resident roster | https://danesheriff.com/Jail | county roster | Official sheriff site links to current resident search/roster. |

## Batch Plan

### Batch 1: quickest first-source wins

Target: add staging-only successful ingestion for the 10 missing states.

Priority order:

1. LA VINE roster family: broad reuse across Louisiana parishes and likely simple roster pages.
2. VT offender locator: official statewide public roster URL.
3. WI Dane County: official current resident roster; likely browse/list flow.
4. RI DOC: official statewide search with disclaimer.
5. NV Clark County: official CCDC search; may require form workflow.
6. OK Payne County: known candidate, likely JS-rendered.
7. CT DOC: official state search.
8. MD DPSCS: official state locator, likely JS-rendered.
9. AK DOC: verify whether a current individual search exists and whether it is accessible without bypass.
10. WI Dane County fallback/alternate: verify the direct current-resident endpoint if the public jail landing page is only navigational.

Deliverables:

- One source review note per state.
- One adapter config or adapter draft per source.
- One dry-run evidence file per source.
- No production enablement until owner approval.

### Batch 2: promote staging states

Target: move staging states into production daily ingestion in review batches of 5 states at a time.

Candidate grouping:

- HTML roster group: AL, IA, IL, MA, MI, MN, MO, MS, ND, NE, NH, NJ, NM, OR, PA, UT, VA, WA, WV
- Search/form group: KS, KY, DE, HI
- Vendor/API group: AR, AZ, CO, IN, ME, SD

Each batch requires approval for:

- source enablement,
- daily schedule,
- public publication predicate,
- rollback route.

### Batch 3: all-jails directory completion

Target: make the directory honest and useful for all 3,531 jails.

Work:

- Keep all 3,531 public directory rows, but label unverified source availability clearly.
- Separate `directory exists` from `roster ingesting`.
- Add source-health and freshness UI before broad promotion.
- Keep counties with no verified roster out of current-inmate sitemap/search promises.

## Guardrails

- No third-party mirror is an authority.
- No CAPTCHA/login/paywall bypass.
- No juvenile, sealed, protected-person, or non-custody publication.
- No raw DOB, residential address, SSN, DL, or mugshot publication without separate review.
- Payment never bypasses correction/removal review.
- Production enablement and daily scheduling remain Red-tier actions requiring explicit owner approval.

## Next Operator Actions

1. Build staging adapter for LA VINE roster pages.
2. Build staging adapter/config for Vermont public roster.
3. Build staging adapter/config for Dane County current resident roster.
4. Prepare first approval packet once each has dry-run evidence.
5. In parallel, audit 5 staging states per batch for promotion readiness.
