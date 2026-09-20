# JailMap next-feature plan

Date: 2026-09-20  
Scope: product and SEO planning only; no production actions authorized or taken.

## 1. Make coverage and freshness self-explanatory

Add a public coverage summary that uses the same eligibility predicate as search and the homepage. Show the last successful source refresh per facility, label stale or temporarily unavailable sources, and stop using archive totals as a proxy for current coverage.

Acceptance criteria:

- One shared service owns current-inmate, county, facility, and state counts.
- Homepage, jail-roster, coverage, state, and county pages agree for the same request window.
- A failed statistics query displays an honest unavailable state and emits an actionable server log.
- Automated tests cover current, stale, suppressed, released, disabled, and unverified records.

## 2. Finish county SEO without publishing thin pages

Complete the facility-to-jurisdiction join described in the SEO reference, then publish a county URL only when it has current public records or verified, substantive facility information. Use real source freshness for sitemap `lastModified` values.

Acceptance criteria:

- Every county URL in the sitemap returns 200 and has a unique title, description, H1, canonical, and breadcrumb.
- Counties without eligible content return 404 and do not appear in the sitemap.
- State pages server-render descriptive links to every eligible county.
- Sitemap failures are logged and never freeze an empty build-time result into production.

## 3. Add source-health transparency

Create a public, non-personal source-status view with facility, jurisdiction, last successful refresh, expected cadence, and a clear stale/error state. Keep operational error detail and credentials private.

Acceptance criteria:

- Status is derived from ingestion run data rather than hard-coded claims.
- Public output contains no personal records, secrets, raw exceptions, or internal endpoints.
- Monitoring alerts when a verified source misses its expected freshness window.
- Each alert names an owner and a documented response path.

## Recommended sequence

1. Extract and test the shared public-statistics query.
2. Reconcile `/coverage`, state pages, and county pages with that query.
3. Implement source-run history and freshness labels.
4. Complete facility enrichment and the county eligibility gate.
5. Validate metadata, structured data, sitemap-to-200 integrity, accessibility, and mobile layout before an approved release.
