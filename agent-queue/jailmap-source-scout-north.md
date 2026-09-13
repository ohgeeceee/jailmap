# Jailmap Source Scout North

Bot: `source-scout-north`

Scope: CT, DE, IA, IL, IN, KS, MA, MD, ME, MI, MN, MO, ND, NE, NH, NJ, NY, OH, PA, RI, SD, VT, WI

Mission: find official jail roster, inmate locator, booking report, or custody
data sources and record them as disabled source leads.

Start with these priority counties:

- IL: Cook, DuPage, Lake, Will, Kane
- NY: New York City, Suffolk, Nassau, Westchester, Erie
- PA: Philadelphia, Allegheny, Montgomery, Bucks, Delaware
- OH: Cuyahoga, Franklin, Hamilton, Summit, Montgomery
- MI: Wayne, Oakland, Macomb, Kent
- MN: Hennepin, Ramsey, Dakota, Anoka
- WI: Milwaukee, Dane, Waukesha, Brown

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
