# National Rollout Summary — 2026-09-17

## Status: 46/50 States with Active Jail Roster Ingestion

### Active States (46)
AL, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, SC, SD, TN, TX, UT, VA, WA, WV, WI, WY

### Missing States (4) — No public roster available
- AK - DOC only offers search form
- NV - Clark County offers search form only
- RI - DOC only offers search form
- VT - DOC only offers search form

### Key Statistics
- Total jurisdictions: 174
- Active staging: 103 jurisdictions
- Public bookings: 5,723
- Total bookings (all visibility): 6,215
- Daily cron: `0 9 * * *` runs all enabled sources

### Adapters Built
- `fl_smartweb_staging` — 20+ FL counties (SmartWeb portal)
- `ocv_json_staging` — 6 counties (Sumner TN, Carter TN, Davidson TN, White TN, Delaware NY, Fresno CA)
- `mt_zuercher_staging` — 6 MT/ID counties (Zuercher portal)
- `html_roster_staging` — 64 counties (generic HTML table parser)
- `pdf_roster_staging` — 2 counties (McLennan TX, Hartford CT)
- `evo_json_staging` — 1 (Cassia ID)
- `citizenrims_portal` — 1 (Big Horn WY)
- `fulton_socrata_staging` — 1 (Fulton GA Socrata)
- `tyler_odyssey_staging` — 1 (Lorain OH)
- `franklin_html_staging` — 1 (Franklin ID)

### Pipeline Fixes (deployed)
- KeyError `charge['id']/bond['id']` → `source_id` (434 failures/week)
- Fulton `updated_at` → `source_updated_at` (142 failures/week)
- Blocked 2 non-roster sources

### Next Steps
1. Get public roster URLs for AK, NV, RI, VT (FOIA or research)
2. Promote tested staging jurisdictions to `staging_only=False` + `enabled=True`
3. Build more vendor adapters (Tyler/Odyssey covers TX, CO)
4. Expand county coverage in active states
