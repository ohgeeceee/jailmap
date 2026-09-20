# National Source Discovery Summary — 2026-09-17

**Covered:** 51 new source leads across 5 large states (TX, FL, CA, NY, PA) + NC

## By State
- **Florida**: 18 leads — dominant vendor is **SmartWeb** (covers 20+ counties: Bradford, Putnam, Escambia, Gadsden, Glades, Hamilton, Sumter, Suwannee, etc.). Also BestJail (Orange County), Hillsborough ArrestInquiry, Pinellas whos-in-jail.
- **Texas**: 5 leads — McLennan County PDF roster, Harris/Travis/Tarrant search portals, Cameron County HTML roster
- **California**: 5 leads — CDCR CIRIS statewide, Alameda/San Bernardino/Ventura/Fresno county inmate locators
- **New York**: 4 leads — NYS Commission of Correction locator list, NYC DOC, Westchester, Oneida County
- **Pennsylvania**: 4 leads — PA DOC statewide, Philadelphia, Lancaster, Westmoreland
- **North Carolina**: 7 leads — 7 counties with P2C HTML rosters (Cumberland, Carteret, Mecklenburg, Rowan, Union, Randolph, Iredell)

## Vendor Families Identified
1. **SmartWeb** (FL, GA, others) — dominant in Florida; identical URL pattern across counties
2. **BestJail** (FL Orange County)
3. **Tyler/Odyssey** (TX, CO — already in adapter registry)
4. **Zuercher Portal** (MT, ID, WA, OR — already in adapter registry)

## Next Steps for Feed-Builder
1. **Florida SmartWeb adapter** — one adapter covers 20+ counties, highest ROI. Same URL pattern: `https://smartweb.<sheriff-domain>/smartwebclient/jail.aspx`
2. **TX McLennan PDF parser** — daily updated PDF roster
3. **NC/PA/CA HTML roster adapters** — these map to the existing `html_roster.py` generic parser with per-county configuration

## Uncovered States (still need discovery)
AL, AK, AZ, AR, CO, CT, DE, HI, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, NE, NH, NJ, NM, NV, ND, OH, OK, OR, RI, SC, SD, TN, UT, VT, VA, WA, WV, WI, WY

**Note:** SmartWeb adapter build should come next — it's one adapter covering 20+ counties in a single state.

## Red-Tier Boundary
All leads above are draft-only (status=staging_only). None have been enabled or added to `records.jurisdictions`. Requires human review before feed-builder creates adapters.
