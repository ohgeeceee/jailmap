# JailMap.com — Jail Roster Source Documentation

## Prototype Adapters / Discovery Leads

These entries are not live public coverage unless they are also present in
`records.jurisdictions` with `review_status='verified'`, `enabled=true`, and
`staging_only=false`. Treat this table as an onboarding backlog: each source
still needs endpoint verification from the production host, source authorization
notes, stable booking identity review, eligibility review, bounded pagination,
failure tests, and a dry run before publication.

| State | County | Records | Source URL | Method |
|-------|--------|---------|------------|--------|
| AZ | Maricopa | 833 | portal.mobileso.com | HTML table (no CAPTCHA) |
| ID | Bonneville | 348 | bonnevillesheriff.com | HTML table |
| ID | Bonner | 76 | bonnerso.org | PDF roster |
| ID | Kootenai | 496 | map.kcgov.us | PDF roster |
| ID | Canyon | 474 | jailroster.canyoncounty.id.gov | Blazor + Playwright |
| ID | Washington | 349 | news.washeriff.net | HTML roster |
| OR | Columbia | 141 | co.columbia.or.us | HTML table |
| OR | Josephine | 100 | jailviewer.josephinecounty.gov | NewWorld + Playwright |
| OR | Umatilla | 20 | ucso.citizenrims.com | CitizenRIMS + Playwright |
| OR | Benton | 104 | sheriff.bentoncountyor.gov | Accordion + Playwright |
| OR | Clatsop | 80 | apps.clatsopcounty.gov | Paginated table + Playwright |
| WA | Spokane | 725 | cp.spokanecounty.gov | iframe + Playwright |
| WA | Whatcom | 298 | whatcomcounty.us | Div table + Playwright |
| WA | Snohomish | 7+ | jailregister.sno911.org | Tyler Tech + Playwright |

Earlier discovery found 3,426+ candidate records across 14 counties, but those
counts are not current production ingestion totals.

## Current Production Coverage

As of 2026-09-13, the active `/root/jailmap` Docker-backed pipeline publishes
one verified source:

| State | County | Public status | Notes |
|-------|--------|---------------|-------|
| GA | Fulton | Enabled, verified, public | Source supplies names, booking numbers and date-only booking dates. Charges, bonds, ages and exact facility assignment are not provided. |

All other discovered sources remain disabled, unverified, staging-only, blocked,
or outside the active ingestion path until reviewed.

## Blocked Sources (CAPTCHA / Turnstile)

| State | County | Source URL | Blocking | Notes |
|-------|--------|------------|----------|-------|
| CA | Los Angeles | app5.lasd.org | reCAPTCHA Enterprise | 9,000+ inmates, search form only |
| CA | San Diego | apps.sdsheriff.net/wij/ | Cloudflare Turnstile | 3,000+ inmates, search form only |
| IL | Cook | iic.ccsheriff.org | reCAPTCHA Enterprise | 5,000+ inmates, search form only |
| TX | Harris | harriscountyso.org | Search form (no roster) | 5,000+ inmates, no public list |

## Common Jail Roster Software Vendors

| Vendor | Counties Using | Method |
|--------|---------------|--------|
| Tyler Technologies (Odyssey/NewWorld/Jail Register) | Many | Playwright + form submission |
| CitizenRIMS | Umatilla OR, others | Playwright |
| EvoGov | Cassia ID, others | JSON API (but some redact names) |
| Power BI Dashboard | Spokane WA | iframe scraping |
| Custom HTML | Bonneville ID, Columbia OR | Direct HTTP + parsing |

## Key Findings

1. **Large counties have public rosters**: LA County (9,000+ inmates), Maricopa, Spokane, Harris, Dallas, etc.
2. **Many require Playwright**: Blazor, React, Angular apps need browser rendering
3. **Some redact names**: Cassia County ID shows #### #### for names
4. **PDF reports**: Many counties publish daily PDF rosters (Bonner ID, Kootenai ID)
5. **Legal restrictions**: Oregon HB 3273 restricts booking photos
6. **No public roster**: Many small counties only offer phone inquiries

## Research Commands

```bash
# Search for county jail roster
web_search "[County] [State] jail roster inmate list public"

# Check if site is JS-rendered
python3 -c "import httpx; r = httpx.get('URL'); print('JS' if '<script' in r.text else 'Static')"

# Test Playwright
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('URL', wait_until='networkidle')
    print(page.inner_text('body')[:2000])
    browser.close()
"
```

## Next Priority Counties

1. **CA**: ~~Los Angeles (9,000+)~~ BLOCKED (reCAPTCHA), ~~San Diego (3,000+)~~ BLOCKED (Cloudflare), Orange (2,000+), Riverside (2,000+)
2. **TX**: ~~Harris (5,000+)~~ BLOCKED (search form), Dallas (4,000+), Tarrant (3,000+), Bexar (3,000+)
3. **FL**: Miami-Dade (4,000+), Broward (3,000+), Palm Beach (2,000+), Hillsborough (2,000+)
4. **NY**: Kings (Brooklyn), Queens, Suffolk, Bronx, Nassau
5. **PA**: Philadelphia (5,000+), Allegheny (2,000+), Montgomery, Bucks, Delaware
6. **AZ**: ~~Maricopa (833+)~~ DONE - portal.mobileso.com
