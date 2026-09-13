# Jailmap Source Scout West

Bot: `source-scout-west`

Scope: AK, AZ, CA, CO, HI, ID, MT, NV, NM, OR, UT, WA, WY

Mission: find official jail roster, inmate locator, booking report, or custody
data sources and record them as disabled source leads.

Start with these priority counties:

- CA: Orange, Riverside, Sacramento, San Bernardino, Alameda
- AZ: Pima, Pinal, Yavapai
- WA: King, Pierce, Clark, Yakima
- OR: Multnomah, Lane, Marion, Deschutes
- NV: Clark, Washoe
- CO: Denver, El Paso, Arapahoe, Adams, Jefferson

Rules:

- Use official county, sheriff, city, jail, court, or open-data sources.
- Do not use third-party mirrors as ingestion authorities.
- Do not bypass captcha, login, paywall, robots, or rate limits.
- Add candidates to `data/official-jail-source-leads.csv`.
- Keep `publication_default` as `staging_only`, `blocked`, or `aggregate_only`.
- Do not enable jurisdictions or run public ingestion.

Checkpoint format:

```text
status:
state:
county:
files_changed:
verification:
source_evidence:
publication_risk:
next_action:
```
