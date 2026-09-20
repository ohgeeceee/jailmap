# JailMap Expansion Report — 2026-09-16

Date: 2026-09-16
Author: jailmap-ops-captain (Hermes)

## Summary

Four new MT adapters and one new SD adapter built, tested, and deployed to staging. National source census completed (2,648 candidates). Draft for remaining MT triage and next-state expansion.

| Action | Type | Status |
|---|---|---|
| `backend/adapters/mt_prairie.py` | Code (Red) | ✅ Live, 8 records staged |
| `backend/adapters/mt_lake.py` | Code (Red) | ✅ Live, 23 records staged |
| `backend/adapters/mt_beaverhead.py` | Code (Red) | ✅ Live, 17 records staged |
| `backend/adapters/mt_lewis_and_clark.py` | Code (Red) | ✅ Live, 165 records staged |
| `backend/adapters/mt_prairie.py` registered | Code (Red) | ✅ `prairie_html_staging` |
| `backend/adapters/mt_lake.py` registered | Code (Red) | ✅ `lake_pdf_staging` |
| `backend/adapters/mt_beaverhead.py` registered | Code (Red) | ✅ `beaverhead_pdf_staging` |
| `backend/adapters/mt_lewis_and_clark.py` registered | Code (Red) | ✅ `lewis_and_clark_pdf_staging` |
| DB: 5 dead Zuercher sources disabled | DB (Red) | ✅ Carbon, Madison, Meagher, Stillwater, Wheatland |
| DB: Prairie/Lake/Beaverhead/L&C adapters set | DB (Red) | ✅ All staging |
| DB: Lincoln County SD adapter set | DB (Red) | ✅ mt_zuercher_staging, 97 records |
| `backend/requirements.txt`: pdfplumber added | Code (Red) | ✅ |
| `backend/db.py`: pool max_size 10→20 | Code (Red) | ✅ Fixes PoolTimeout |
| National census (2,648 candidates) | Analysis (Green) | ✅ 65 ingest candidates found |
| MT triage: remaining `standard_json` counties | Analysis (Green) | Drafted below |
| National vendor_portal adapter plan | Analysis (Green) | Drafted below |
| SD expansion: next-state plan | Analysis (Green) | Drafted below |

## 1. MT Triage — Remaining Broken `standard_json` Sources

10 MT counties still have `standard_json` adapter but broken/non-JSON URLs:

| County | URL | Actual Content | Action Needed |
|---|---|---|---|
| Beaverhead | wp-content/uploads/...Jail-Roster.pdf | PDF (text-based) | ✅ Fixed — `beaverhead_pdf_staging` |
| Carter | cartercountysheriff.us/inmate-search | Wappler SPA (JS render) | Needs Playwright — blocked |
| Cascade | cascadecountymt.gov/314/Inmate-Roster | HTML page, no roster link | Outreach |
| Chouteau | chouteaucountysheriff.com/ | HTML page, no roster link | Outreach |
| Custer | custercountymt.gov/emergency-enforcement/sheriff/ | HTML page with PDF link | Could fix — PDF linked |
| Fergus | fergusmt.gov/detention-center-roster | HTML page, no roster link | Outreach |
| Gallatin | gallatin-so-mt.zuercherportal.com/#/inmates | Zuercher maintenance | Transient — self-healing |
| Glacier | glaciercountymt.gov/category/jail-roster/ | HTML page, no roster link | Outreach |
| Lewis and Clark | lccountymt.gov/Sheriff/Detention-Center | PDF (jail_roster.pdf) | ✅ Fixed — `lewis_and_clark_pdf_staging` |
| Silver Bow | co.silverbow.mt.us/3274/Detention-Center | HTML page, no roster link | Outreach |
| Valley | valleycountymt.gov/1288/Jail-Roster | docaccess.com JS PDF viewer | Needs Playwright — blocked |

**Quick win**: Custer County has a PDF link on its page (`wp-content/uploads/2026/09/CCDF_Daily_Roster_...pdf`). Build a `mt_custer.py` adapter that scrapes the page for the PDF URL and parses it.

**Remaining 7 counties** with no public roster → FOIA/outreach.

## 2. National Source Census Results

2,648 `.gov` domains probed across all 50 states:

| Access Class | Count | Meaning |
|---|---|---|
| no_roster_found | 1,348 | Homepage has no roster link |
| search_form | 426 | Search form (needs outreach/adapter) |
| unreachable | 289 | Domain doesn't resolve |
| blocked | 256 | HTTP 403/406 (WAF, rate limit) |
| login_required | 89 | Login wall |
| captcha_gated | 83 | CAPTCHA |
| robots_disallowed | 52 | robots.txt blocks |
| **vendor_portal** | **44** | Vendor portal (Zuercher, Tyler, etc.) |
| **html_roster** | **19** | Direct HTML roster |
| **pdf_roster** | **2** | PDF roster |

**Ingest candidates: 65 of 2,648 (2.5%)**

### Vendor family breakdown (from 44 vendor_portal):

| Vendor | Count | States |
|---|---|---|
| Zuercher | 12 | AL, MT, SD, IA, SC, IL |
| Socrata/open data | 10 | AL, CA, CO, MT, OH |
| CitizenRIMS | 5 | CA |
| SmartWEB | 2 | CO |
| Other/unknown | 15 | various |

### Recommended adapter build priority:

1. **Zuercher** — 12 counties, one adapter (`mt_zuercher.py` exists, just register new states)
2. **Tyler/Odyssey** — TX, CO counties
3. **SmartWEB** — CO, FL, GA counties
4. **Socrata** — open data portals (generic adapter possible)

### Top candidate states (most ingest candidates):

| State | Candidates | Notes |
|---|---|---|
| MO | 8 | Mostly search_form |
| CA | 7 | 5 CitizenRIMS, 2 other |
| GA | 5 | Mixed |
| MT | 5 | 3 vendor_portal (2 zuercher already), 2 html_roster |
| OH | 5 | Mixed vendor |
| AL | 4 | 2 zuercher, 1 socrata, 1 html_roster |
| TX | 4 | Mixed |

## 3. SD Expansion — Next State

### Current SD status

| County | Adapter | Status |
|---|---|---|
| Lincoln County | `mt_zuercher_staging` | ✅ 97 records staged |
| Minnehaha | `custom_html` | Unverified (source URL works) |

### SD national census results

| Access Class | Counties |
|---|---|
| vendor_portal | Brookings (zuercher) |
| search_form | Fall River |
| unreachable | 6 counties |
| no_roster_found | remaining |

### Immediate actions for SD:

1. **Brookings County** — zuercher portal detected. Add to DB as staging source.
2. **Minnehaha County** — verify `custom_html` adapter works, promote to verified.
3. **Fall River County** — search_form, needs outreach or adapter.

### Recommended next-state priority (by ingest candidate count):

1. **MO** (8 candidates) — mostly search_form but large county count
2. **CA** (7 candidates) — 5 CitizenRIMS (one adapter = 5 counties)
3. **OH** (5 candidates) — mixed, mix of vendor and search_form
4. **AL** (4 candidates) — 2 zuercher (easy wins)

## Files Written

- `/root/jailmap/backend/adapters/mt_prairie.py` — Prairie County ASP.NET roster
- `/root/jailmap/backend/adapters/mt_lake.py` — Lake County PDF roster
- `/root/jailmap/backend/adapters/mt_beaverhead.py` — Beaverhead PDF roster
- `/root/jailmap/backend/adapters/mt_lewis_and_clark.py` — Lewis & Clark PDF roster
- `/root/jailmap/tests/test_mt_prairie.py` — 7 unit tests
- `/root/jailmap/tests/test_mt_lake.py` — 5 unit tests
- `/root/jailmap/tests/test_mt_pdf_adapters.py` — 5 unit tests (Beaverhead + L&C)
- `/root/jailmap/data/national/census-dotgov-v4.csv` — full national census (2,648 rows)

## Evidence

```
MT / Prairie: 8 validated records; staged privately
MT / Lake: 23 validated records; staged privately
MT / Beaverhead: 17 validated records; staged privately
MT / Lewis and Clark: 165 validated records; staged privately
SD / Lincoln County: 97 validated records; staged privately

New adapter dry runs:
MT / Prairie: 8 validated records; dry run, no writes
MT / Lake: 23 validated records; dry run, no writes
MT / Beaverhead: 17 validated records; dry run, no writes
MT / Lewis and Clark: 165 validated records; dry run, no writes

Tests:
Ran 17 tests in 0.004s — OK
```

## Next Steps (pending approval)

- [ ] A — Build `mt_custer.py` adapter (PDF link on page, parse PDF)
- [ ] B — Register Brookings County SD as zuercher staging source
- [ ] C — Promote Minnehaha SD to verified (test existing adapter)
- [ ] D — For CA CitizenRIMS counties, investigate one portal and build adapter
- [ ] E — For AL Zuercher counties, register and stage
- [ ] F — FOIA/outreach letters for 7 MT counties with no public roster
