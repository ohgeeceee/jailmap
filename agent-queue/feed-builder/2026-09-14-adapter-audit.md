# feed-builder - adapter registration audit

Generated 2026-09-14 12:00Z by `bots/`.

Green tier: reads the repository and writes this digest only. It does not edit `backend/ingest.py`, run ingestion, or change any source.

- Adapter modules present: **44**
- Registered in `ingest.py`: **14** (ADAPTERS dict found at offset 2459)
- Without `NotImplementedError`: **44**
- **Orphaned (real module, not registered): 44**
- Scaffolding modules raising `NotImplementedError`: 0
- Real modules with no fetch/parse entry point: 2

## Registration candidates (orphaned)

| Module | Lines | Entry point |
|---|---|---|
| alabama | 415 | yes |
| alabama_counties | 98 | no |
| benton_accordion | 98 | yes |
| bexar_county_tx | 83 | yes |
| bonner_pdf | 180 | yes |
| bonneville_html | 82 | yes |
| canyon_html | 146 | yes |
| cassia_json | 95 | yes |
| clatsop_table | 114 | yes |
| columbia_or_html | 96 | yes |
| cook_county_il | 83 | yes |
| cuyahoga_county_oh | 83 | yes |
| dallas_county_tx | 83 | yes |
| florida | 179 | yes |
| florida_smartweb | 194 | yes |
| franklin_html | 101 | yes |
| fulton_county_ga | 83 | yes |
| harris_county_tx | 83 | yes |
| html_roster | 298 | yes |
| idaho | 219 | no |
| jefferson_html | 73 | yes |
| josephine_html | 120 | yes |
| kootenai_pdf | 179 | yes |
| los_angeles_lasd | 84 | yes |
| maricopa_html | 137 | yes |
| maricopa_roster | 111 | yes |
| mecklenburg_county_nc | 83 | yes |
| minnehaha_html | 82 | yes |
| mt_flathead | 136 | yes |
| mt_missoula | 218 | yes |
| mt_yellowstone | 147 | yes |
| mt_zuercher | 162 | yes |
| orange_county_fl_bestjail | 83 | yes |
| owyhee_pdf | 156 | yes |
| power_html | 73 | yes |
| san_diego_sdsheriff | 83 | yes |
| snohomish_jailregister | 116 | yes |
| socrata | 205 | yes |
| spokane_roster | 122 | yes |
| travis_county_tx | 83 | yes |
| umatilla_citizenrims | 124 | yes |
| wake_county_nc | 83 | yes |
| washington_html | 68 | yes |
| whatcom_roster | 107 | yes |

A candidate still needs a dry run against a live source before registration. The registry key must match the value a jurisdiction row uses in `records.jurisdictions.adapter`.

## Next action

Draft a registration diff for the orphaned modules that still target live sources, each with a dry-run transcript, and hand it over as a Red-tier draft for human approval. Never register blind.
