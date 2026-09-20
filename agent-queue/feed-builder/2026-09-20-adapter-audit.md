# feed-builder - adapter registration audit

Generated 2026-09-20 12:00Z by `bots/`.

Green tier: reads the repository and writes this digest only. It does not edit `backend/ingest.py`, run ingestion, or change any source.

- Adapter modules present: **60**
- Registered in `ingest.py`: **29** (ADAPTERS dict found at offset 2860)
- Without `NotImplementedError`: **60**
- **Orphaned (real module, not registered): 60**
- Scaffolding modules raising `NotImplementedError`: 0
- Real modules with no fetch/parse entry point: 3

## Registration candidates (orphaned)

| Module | Lines | Entry point |
|---|---|---|
| alabama | 415 | yes |
| alabama_counties | 98 | no |
| benton_accordion | 97 | yes |
| bexar_county_tx | 82 | yes |
| bonner_pdf | 179 | yes |
| bonneville_html | 81 | yes |
| canyon_html | 146 | yes |
| cassia_json | 95 | yes |
| citizenrims | 140 | yes |
| clatsop_table | 113 | yes |
| columbia_or_html | 96 | yes |
| cook_county_il | 82 | yes |
| cuyahoga_county_oh | 82 | yes |
| dallas_county_tx | 82 | yes |
| evo_json | 99 | yes |
| fl_smartweb | 197 | yes |
| florida | 179 | yes |
| florida_smartweb | 194 | yes |
| franklin_html | 104 | yes |
| fulton_county_ga | 82 | yes |
| gov_website | 232 | yes |
| harris_county_tx | 82 | yes |
| html_roster | 367 | yes |
| idaho | 238 | no |
| idaho_assert | 9 | no |
| jefferson_html | 72 | yes |
| josephine_html | 120 | yes |
| kootenai_pdf | 178 | yes |
| los_angeles_lasd | 83 | yes |
| maricopa_html | 137 | yes |
| maricopa_roster | 111 | yes |
| mecklenburg_county_nc | 82 | yes |
| minnehaha_html | 81 | yes |
| mt_beaverhead | 164 | yes |
| mt_carter | 151 | yes |
| mt_fergus | 144 | yes |
| mt_flathead | 135 | yes |
| mt_garfield | 104 | yes |
| mt_lake | 138 | yes |
| mt_lewis_and_clark | 135 | yes |
| mt_missoula | 218 | yes |
| mt_prairie | 186 | yes |
| mt_yellowstone | 147 | yes |
| mt_zuercher | 163 | yes |
| ocv_json | 194 | yes |
| orange_county_fl_bestjail | 82 | yes |
| owyhee_pdf | 155 | yes |
| pdf_roster | 133 | yes |
| power_html | 72 | yes |
| san_diego_sdsheriff | 82 | yes |
| snohomish_jailregister | 116 | yes |
| socrata | 205 | yes |
| spokane_roster | 122 | yes |
| travis_county_tx | 82 | yes |
| tyler_jailtracker | 20 | yes |
| tyler_odyssey | 74 | yes |
| umatilla_citizenrims | 124 | yes |
| wake_county_nc | 82 | yes |
| washington_html | 68 | yes |
| whatcom_roster | 107 | yes |

A candidate still needs a dry run against a live source before registration. The registry key must match the value a jurisdiction row uses in `records.jurisdictions.adapter`.

## Next action

Draft a registration diff for the orphaned modules that still target live sources, each with a dry-run transcript, and hand it over as a Red-tier draft for human approval. Never register blind.
