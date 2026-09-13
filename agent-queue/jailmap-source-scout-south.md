# Jailmap Source Scout South

Bot: `source-scout-south`

Scope: AL, AR, FL, GA, KY, LA, MS, NC, OK, SC, TN, TX, VA, WV

Mission: find official jail roster, inmate locator, booking report, or custody
data sources and record them as disabled source leads.

Start with these priority counties:

- TX: Harris, Dallas, Tarrant, Bexar, Travis, Collin, Denton
- FL: Miami-Dade, Broward, Palm Beach, Hillsborough, Orange, Pinellas
- GA: Fulton, Gwinnett, Cobb, DeKalb, Clayton
- NC: Mecklenburg, Wake, Guilford, Forsyth, Durham
- TN: Shelby, Davidson, Knox, Hamilton
- VA: Fairfax, Prince William, Virginia Beach, Chesterfield

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
