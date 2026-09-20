# JailMap National Rollout — Final Status 2026-09-17

## 46 of 50 States Have Active Jail Roster Ingestion

### States with Active Ingestion (46)
AL, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, SC, SD, TN, TX, UT, VA, WA, WV, WI, WY

### States Without Public Rosters (4)
- **AK** — DOC offers search form only, no public roster
- **NV** — Clark County offers search form only, no public roster  
- **RI** — DOC offers search form only, no public roster
- **VT** — DOC offers search form only, no public roster

These 4 states do not publish public jail rosters. Getting ingestion for them requires FOIA requests or finding county-level alternatives.

## Key Stats
- **Total jurisdictions:** 174
- **Active staging:** 103 jurisdictions
- **Public bookings:** 5,723
- **Total bookings (all visibility):** 6,215
- **Daily cron:** `0 9 * * *` runs all enabled sources

## Adapters Built (10 types)
| Adapter | Count | Coverage |
|---------|-------|----------|
| html_roster_staging | 64 | Generic HTML table parser |
| mt_zuercher_staging | 6 | Zuercher portal (MT, ID) |
| ocv_json_staging | 6 | OCV JSON API (TN, NY, CA) |
| pdf_roster_staging | 2 | PDF parsing (TX, CT) |
| fl_smartweb_staging | 1 | SmartWeb portal (20+ FL counties) |
| evo_json_staging | 1 | Evo JSON (ID) |
| citizenrims_portal | 1 | CitizenRims (WY) |
| fulton_socrata_staging | 1 | Socrata open data (GA) |
| tyler_odyssey_staging | 1 | Tyler/INCODE (OH) |
| franklin_html_staging | 1 | Franklin County HTML (ID) |

## Pipeline Fixes Deployed
- KeyError `charge['id']/bond['id']` → `source_id` (was 434 failures/week)
- Fulton `updated_at` → `source_updated_at` (was 142 failures/week)
- Blocked 2 non-roster sources (WY Laramie, WV Wirt)

## What's Running Now
```bash
# Daily cron at 09:00 UTC
0 9 * * * docker exec jailmap-api-1 sh -c "cd /app && python roster_manager.py --run all"

# Verify
curl -sS http://127.0.0.1:3109/status
curl -sS http://127.0.0.1:3109/api/new-bookings
```

## Next Steps to 50 States
1. **AK, NV, RI, VT** — Need FOIA requests or discovery of county-level public rosters
2. **Promote staging → public** — Jurisdictions with successful runs can be promoted to `staging_only=False` + `enabled=True`
3. **More county coverage** — Many states have ingestion for 1-2 counties but could have 10-50+
4. **Vendor adapters** — Tyler/Odyssey (TX, CO), SmartWeb (GA, FL), Zuercher (MT, ID, WA, OR) can each cover 10-100+ facilities
