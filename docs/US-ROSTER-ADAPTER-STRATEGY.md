# United States jail-roster adapter strategy

Date: 2026-09-20

## Routing order

Use the cheapest reliable source type first. Never add browser automation until direct HTTP and public network endpoints have been ruled out.

1. Official JSON/REST endpoint: preserve the vendor booking ID, page deterministically, and cap pages and records.
2. Official server-rendered HTML table/list: use an explicit column map when body and header counts differ. Follow detail pages only on the same configured host.
3. Official text PDF: extract text, retain the source timestamp, and quarantine batches when the layout fingerprint changes.
4. Public JavaScript/ASP.NET form: inspect its public network calls first; otherwise use bounded Playwright form submission.
5. Scanned PDF: OCR only in a quarantined pipeline with confidence thresholds and human review.
6. CAPTCHA, authentication, VINE/Appriss, or terms-restricted portal: do not bypass controls. Seek an API/data agreement or mark the source blocked.

## Current repository inventory

- 60 legacy adapter modules exist, with mixed maturity and schemas.
- Structured discovery currently covers 45 Idaho entries and 12 South Dakota entries; it is not yet a national inventory.
- Idaho contains 15 rows marked active, including one duplicate Idaho County entry.
- South Dakota contains seven usable active sources after removing a Minnesota URL incorrectly assigned to South Dakota.
- The modular pipeline currently has one live-validated, explicitly mapped facility adapter: Minnehaha County, South Dakota.

## Highest-value next adapters

| Priority | Source | Recommended driver | Reason / gate |
|---|---|---|---|
| 1 | Power County, Idaho | HTML list + same-host detail pages | Small, public, stable list; the legacy parser already identifies booking-detail links. Add charge/bond detail and real booking timestamps before promotion. |
| 2 | Codington County, South Dakota | Text PDF | The official page links a current-inmates PDF. Store the county's warning that the list is incomplete; never interpret absence as release. |
| 3 | Kootenai County, Idaho | Text PDF | Rich charge, bond, incarceration, and scheduled-release fields. Requires a defensible stable booking key because the legacy adapter emits none. |
| 4 | Ada County, Idaho | HTML/ASP.NET | Official daily adult roster. Build deterministic alphabet/page traversal and verify the current form lifecycle. |
| 5 | Jefferson and Franklin Counties, Idaho | PHP/HTML detail pages | Existing source-specific adapters provide a starting point; port them with fixtures and layout fingerprints. |
| 6 | Bonner and Brookings Counties | PDF discovery + text PDF | Resolve the current official PDF URL each run, restrict redirects to approved hosts, then parse a versioned layout. |
| 7 | Pennington County, South Dakota | ASP.NET or public backing API | Use Playwright only if no stable public request endpoint is available. |

## Acceptance gate for every facility

- Official source ownership and access policy verified.
- Adult/public roster scope documented; juveniles, protected holds, and noncustodial populations excluded.
- Stable `(facility_id, booking_number)` identity demonstrated. Synthetic IDs require explicit review.
- Source timezone and booking-date format covered by fixtures.
- Charges and bonds maintain their relationship; textual states such as `No Bond` are not converted to zero.
- Layout fingerprint, row-count bounds, duplicate detection, and missing-field thresholds enabled.
- Dry runs report aggregate counts only. Sample inmate data must not appear in logs, fixtures, or screenshots.
- Two identical runs prove idempotency before scheduling.
- Records remain staged until review and publication safeguards approve them.

## National discovery plan

Build state worklists from official sheriff and county domains, then classify each source as `json`, `html`, `text_pdf`, `scanned_pdf`, `browser`, `agreement_required`, or `no_public_roster`. Track source owner, canonical URL, facility served, update cadence, adult-only statement, robots/terms review, last verification time, layout fingerprint, and adapter/test status. Prioritize expected current population divided by adapter and maintenance cost—not simply county count.
