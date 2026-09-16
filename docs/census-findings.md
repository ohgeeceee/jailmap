# Source census — first national pass

> ## Correction, same day: `html_roster` and `search_form` were over-reported
>
> Passes 1–4 below classified `html_roster` on **keyword presence** — if a page
> mentioned "inmate" and had no `<form>`, it got the label. That is not evidence of a
> roster. Verified directly: five census-labelled `html_roster` targets
> (`houstoncosoal.gov`, `dallascosoar.gov`, `sonomasheriff.org`, `jeffcosheriffco.gov`,
> `sheriff.baldwincountyal.gov`) contained **zero `<table>` elements**. They are
> homepages that mention inmates.
>
> The classifier now requires a table carrying a person-identity column, using the
> same column mapping as the production adapter (`roster_tables()` in
> `fingerprint_sources.py`). `search_form` is similarly loose — a form plus a keyword
> mention — and should be read as "possibly searchable", not "confirmed roster search".
>
> **Treat every `html_roster` and `search_form` count below as an upper bound.** The
> trustworthy figures are the re-run in "Fifth pass" at the end of this document.

Generated 2026-09-14 by `scripts/national/fingerprint_sources.py`.
Input: `data/national/candidates-national.csv` (132 candidates, 15 states, from the research
catalogs after excluding third-party mirrors). Run with `--no-follow`.

## Result: 132 jails classified

| Access class | Count | % | Meaning |
|---|---:|---:|---|
| `search_form` | 49 | 37.1% | Roster behind a search form — adapter needs form/pagination work |
| `no_roster_found` | 18 | 13.6% | Site loaded, no roster on the pages probed |
| `html_roster` | 14 | 10.6% | Static roster table — easiest to adapt |
| `blocked` | 11 | 8.3% | 401/403/429 — access denial, outreach not code |
| `vendor_portal` | 9 | 6.8% | Vendor platform detected (see below) |
| `unreachable` | 8 | 6.1% | DNS/connect failure — host is dead or moved |
| `http_404` | 7 | 5.3% | Path gone; site may exist elsewhere |
| `captcha_gated` | 6 | 4.5% | CAPTCHA. Stop. Outreach, never bypass |
| `robots_disallowed` | 5 | 3.8% | `robots.txt` forbids us. Obeyed |
| `pdf_roster` | 4 | 3.0% | PDF roster — parseable |
| `login_required` | 1 | 0.8% | Behind a login. Stop |

**Buckets that matter:**

- **Ingest candidates: 76 / 132 (57.6%)** — `search_form` + `html_roster` + `vendor_portal` + `pdf_roster`
- **Gated, needs outreach: 23 (17.4%)** — `blocked` + `captcha_gated` + `robots_disallowed` + `login_required`
- **Needs deeper discovery: 33 (25.0%)** — `no_roster_found` + `unreachable` + `http_404`

## Vendor family histogram

```
smartweb            4
zuercher            3
socrata_open_data   2
```

## The uncomfortable finding

**The vendor-family thesis is weaker at county level than expected.** Only 9 of 132 (6.8%) hit a
detected vendor platform. The dominant pattern is bespoke county-built sites: `search_form` +
`html_roster` = **63 of 132 (47.7%)**.

The reasoning behind the vendor strategy still holds — a Zuercher portal is a Zuercher portal
everywhere — but at the *county* tier these are small sheriff sites, not enterprise portals. The
big vendor platforms cluster in larger metros and state DOC systems. So:

- Day 3 should **not** commit to a vendor adapter yet on this evidence.
- The highest-yield first adapter may be a **generic HTML roster + search-form adapter**, because
  that is where the volume actually is — even though it is harder to generalise.
- The vendor histogram needs a bigger, better-distributed sample before it can be trusted.

## Sampling bias — read before deciding Day 3

The sample is **69% Florida + Idaho** (49 + 42 of 132). That is not nationally representative, and
any adapter choice made from this histogram would be tuned to two states.

The fix is already identified: the CISA `.gov` registry maps **2,089 of 3,143 counties (66.5%)** to
an official government domain, including 267 dedicated sheriff domains. Re-running the census
against that distribution is what makes the histogram trustworthy. **Do this before building the
Day 3 adapter.**

## Fifth pass — corrected classifier (authoritative numbers)

Generated 2026-09-14. Same input as pass 3 (`candidates-dotgov.csv`, 2,648 resolving domains,
`--no-follow`) but with the classifier fixed to require real roster structure. Output:
`data/national/census-dotgov-v2.csv`. **These supersede passes 1–4 for `html_roster`.**

| Access class | v2 | pass 3 | change |
|---|---:|---:|---|
| `no_roster_found` | 1,645 (62.1%) | 1,558 (58.8%) | +87 |
| `unreachable` | 293 | 294 | — |
| `blocked` | 255 (9.6%) | 274 | −19 |
| `search_form` | 193 (7.3%) | 194 | — |
| `login_required` | 77 | 77 | — |
| `captcha_gated` | 61 | 61 | — |
| `robots_disallowed` | 47 | 47 | — |
| `vendor_portal` | 23 | 23 | — |
| **`html_roster`** | **5 (0.2%)** | **72 (2.7%)** | **−67** |

Vendor family unchanged: `socrata_open_data` 7, `citizenrims` 5, `zuercher` 5,
`tyler_jailtracker` 4, `tyler_odyssey` 2.

### What this means

**Only 5 of 2,648 official county domains expose a directly-parseable roster table on their
homepage.** The other 67 "html_roster" hits were homepages that mentioned inmates. Confirmed by
direct inspection — `houstoncosoal.gov`, `dallascosoar.gov`, `sonomasheriff.org`,
`jeffcosheriffco.gov`, `sheriff.baldwincountyal.gov` all contain zero `<table>` elements.

This weakens the recommendation I made after pass 3 ("build the HTML-roster parser first, 72
targets need no discovery"). The parser is still correct and still shipped, but its *target list*
was fictional. The honest position now:

- `search_form` (193) is the largest actionable class, but it is itself an unverified label —
  "a form plus a keyword mention". It needs the same structural rigour before it can be called a
  roster search, and each one needs bespoke form/pagination work.
- `vendor_portal` (23) remains too thin to lead with.
- `no_roster_found` (62%) at homepage depth is not evidence of absence. It is the queue for the
  two-hop sheriff crawl.

There is no large, easy, already-catalogued pile of rosters. That is the finding. Coverage grows
through the two-hop crawl, per-source adapter work, and outreach — not by flipping a switch on
sources that were already sitting there.

## Fourth pass — the follow pass, and what it proved

Generated 2026-09-14. Input: `data/national/candidates-noroster.csv` — the 1,558 sites classified
`no_roster_found` at homepage depth in pass 3. Output: `data/national/census-follow.csv`.
Re-probed with roster-path following (6 common paths per site), `--concurrency 12`, 20 minutes.

| Access class | Count | % |
|---|---:|---:|
| `no_roster_found` | 1,480 | 95.0% |
| `search_form` | 45 | 2.9% |
| `html_roster` | 23 | 1.5% |
| `unreachable` | 6 | 0.4% |
| `blocked` | 3 | 0.2% |
| `http_504` | 1 | 0.1% |

**Only 68 of 1,558 (4.4%).** Guessed paths recovered almost nothing.

### Why — and this is the finding that matters

A 12-site diagnostic (`scripts/national/_diag_follow.py`) established that the probe was working
correctly and the technique was wrong:

```
AL Calhoun County   home=200 /sheriff=200 links=92  sheriff_links=1 other_domain=1
AL Baldwin County   home=200 /sheriff=404 links=76  sheriff_links=0
AL Cullman County   home=200 /sheriff=404 links=135 sheriff_links=0
AL Chambers County  home=200 /sheriff=404 links=133 sheriff_links=14
AL Blount County    home=200 /sheriff=200 links=134 sheriff_links=2 other_domain=2
```

`/sheriff` returns **404 on 8 of 12** commission sites — the guessed path does not exist. Where a
real link exists it is `/departments/sheriffs-department`, `/31/Sheriffs-Department`, or a
different domain entirely (`calcoso.org`, `blountalsheriff.org`).

Checked directly, `calcoso.org` (Calhoun County Sheriff, AL) has **24 roster links on its own
homepage** — `/jail/`, `/divisions-corrections/`, `/inmate-accounts/`. So the chain is:

```
county commission domain  ->  link to sheriff domain  ->  roster page on the sheriff site
```

That is **two hops**, often across domains. A path-guessing probe cannot reach it, and neither can
link-following that only follows the links it finds on one page.

Link-following was added (`roster_links()` + `follow_links()`) and tested on the same 12 sites: it
recovered 2 where path-guessing recovered 0 — better, but still not enough, because most commission
sites do not link their sheriff at all (8 of 12 had no sheriff link).

### Honest conclusion about this approach's ceiling

The `.gov` registry is an excellent **ownership** map and a mediocre **roster** map:

| | Value |
|---|---|
| Counties with a live official domain | ~2,300 (87.1% of resolving domains) |
| Ingest candidates found by probing | **289** (194 search_form, 72 html_roster, 23 vendor_portal) |
| Recoverable by path guessing | 68 more (4.4% of the remainder) |
| Gated, needs outreach | ~459 (17.3%) |

**~290 county sources is the realistic yield from this technique**, not 2,300. Getting further
requires a real two-hop crawl (commission → sheriff → roster) with per-hop robots checks, which is a
different tool from a census probe, and it will still miss every county whose government does not
publish or link a roster.

That is not a failure — it is the number that replaces guesswork. The next unit of work is a
**sheriff-link crawler**, and the honest expectation for it is hundreds more sources, not thousands.

### What to do next, in order

1. **Build the generic HTML-roster table parser** for the 72 `html_roster` sources already found.
   They need no further discovery. This is the cheapest real coverage win.
2. **Look hard at `socrata_open_data` (7 and counting)** — open-data portals are a documented JSON
   API, no scraping, one adapter, and they reliably publish machine-readable data.
3. **Write the two-hop sheriff-link crawler** for the ~1,500 `no_roster_found` commission sites.
   Budget it as a crawl (bounded depth 2, per-host rate limits, robots per hop), not a probe.
4. **Start the outreach list** — 459 gated domains plus every county with no published roster. This
   is where `montanablotter-jail-roster-agency-outreach` applies, and it is the only path to those
   counties.

## Third pass — full national registry census (2,648 domains)

Generated 2026-09-14. Input: `data/national/candidates-dotgov.csv` — all 2,648 resolving `.gov`
domains from the county join (2,462 county/commission + 186 sheriff). Output:
`data/national/census-dotgov.csv`. Run at `--concurrency 12`, completed in 12.5 minutes.

| Access class | Count | % |
|---|---:|---:|
| `no_roster_found` | 1,558 | 58.8% |
| `unreachable` | 294 | 11.1% |
| `blocked` | 274 | 10.3% |
| `search_form` | 194 | 7.3% |
| `login_required` | 77 | 2.9% |
| `html_roster` | 72 | 2.7% |
| `captcha_gated` | 61 | 2.3% |
| `robots_disallowed` | 47 | 1.8% |
| `vendor_portal` | 23 | 0.9% |
| `http_*` errors (4xx/5xx) | 32 | 1.2% |

Vendor family: `socrata_open_data` 7, `citizenrims` 5, `zuercher` 5, `tyler_jailtracker` 4,
`tyler_odyssey` 2.

**Reachable: 2,306 / 2,648 (87.1%).**

### The 58.8% is a measurement artifact — do not read it as "no roster"

This pass ran `--no-follow`, so **only the homepage was checked**. A county's roster is essentially
never on its homepage; it lives at `/inmate-search`, `/sheriff/`, `/jail/`, `/corrections/`. So
`no_roster_found` here means *"not on the homepage"*, not *"this county publishes nothing"*.

Reading it as "59% of counties have no roster" would be exactly the kind of false conclusion this
whole exercise exists to prevent. The second pass on sheriff domains shows the same shape (19.3%
`no_roster_found` at homepage depth) and it drops sharply once roster paths are tried.

The follow-up pass exists to answer the real question:
`data/national/candidates-noroster.csv` (1,558 sites) re-probed with roster-path following.

### What this pass does establish

1. **Liveness at scale**: 87.1% of registered `.gov` county domains actually serve a site. That is
   the honest ceiling for this source, and it is better than the 63.3% county-level rate suggested
   (commission domains are more likely to be live than niche sheriff domains).
2. **289 ingest candidates found at homepage depth alone** — 194 `search_form` + 72 `html_roster` +
   23 `vendor_portal` (10.9% of the sample). These need no further discovery; they are directly
   adaptable.
3. **17.3% are gated** — 274 `blocked` + 77 `login_required` + 61 `captcha_gated` + 47
   `robots_disallowed`. That is an outreach problem, not an engineering one, and it is roughly one
   in six domains.
4. **The vendor histogram stays thin**: 23 of 2,648 (0.9%). Even counting the Tyler family
   (`jailtracker` 4 + `odyssey` 2), no single vendor comes close to justifying an adapter-first
   strategy at the county tier. `socrata_open_data` leading at 7 is notable — those are open-data
   portals, the most tractable adapter of all, and worth a dedicated look.

### Revised adapter recommendation

Evidence from all three passes now points the same way:

| Target | Volume | Why |
|---|---|---|
| **Socrata open-data portals** | 7 + more once sheriffs are followed | Clean JSON API, one adapter, no scraping |
| **HTML roster tables** | 72 + more from the follow pass | Static tables, generalisable parser |
| **`search_form` sites** | 194 | Highest volume, but needs form/pagination work |
| Vendor portals | 23 | Too thin nationally to lead with |

Build the generic **HTML-roster table parser** first: it is simpler than a search-form adapter,
covers `html_roster` plus a large share of Socrata-adjacent pages, and every pass shows those
sources are directly adaptable without further discovery.

## Second pass — national sheriff-domain sample (decision-grade)

Generated 2026-09-14. Input: `data/national/candidates-sheriff.csv` — **270 sheriff/sheriff's-office
`.gov` domains across 42 states** (max state concentration 8.9%, vs 69% FL+ID in the first pass).
Output: `data/national/census-sheriff.csv`. This is the sample the first pass should have been.

| Access class | Count | % |
|---|---:|---:|
| `unreachable` | 113 | 41.9% |
| `no_roster_found` | 52 | 19.3% |
| `search_form` | 32 | 11.9% |
| `html_roster` | 31 | 11.5% |
| `blocked` | 15 | 5.6% |
| `robots_disallowed` | 11 | 4.1% |
| `vendor_portal` | 7 | 2.6% |
| `http_406` | 6 | 2.2% |
| `login_required` / `captcha_gated` / `http_404` | 1 each | 0.4% each |

Vendor family: `citizenrims` 4, `zuercher` 2, `tyler_jailtracker` 1.

### Why 41.9% unreachable is not a bug

Verified with `dig @1.1.1.1` against the system resolver — both agreed on every NXDOMAIN. The CISA
`.gov` registry lists **registered** domains, not live ones; 535 of 3,183 (16.8%) never resolve at
all, and 84 of 270 sheriff domains (31%) are dead. Agencies register defensively and deploy later.
`build_candidates.py --dns-check` now filters these out before requests are spent.

### What this actually tells us

Reachable sheriff domains: **157 of 270 (58.1%)**. Of those:

- **Ingest candidates: 70 (25.9% of sample)** — `search_form` 32 + `html_roster` 31 + `vendor_portal` 7
- **Gated, needs outreach: 28 (10.4%)** — `blocked` 15 + `robots_disallowed` 11 + 2 others
- **No roster found: 52 (19.3%)** — site loads, roster not on the pages probed

Two conclusions, and the second one matters more:

1. **The vendor-family strategy is still not validated.** Across 270 nationally distributed sheriff
   domains, only 7 hit a detected vendor platform. Even including the first pass, the vendor
   histogram stays too thin to justify building a vendor adapter as the *first* move.
2. **The volume is in bespoke sites.** `search_form` + `html_roster` = 63 counties here, and 63 of
   132 in the first pass. A generic HTML-roster + search-form adapter targets where the sources
   actually are, even though it is harder to generalise than one vendor adapter.

Also worth noting: New York returned `robots_disallowed` on 5 of 14 counties — 36% of its sample.
Robots policy is jurisdiction-specific and cannot be assumed from a vendor or a state.

### Next census run

1. Run `--dns-check` first so the denominator reflects reachable hosts.
2. Census the rank-2 county/commission domains (`candidates-dotgov.csv`, 2,462 resolving) — the
   sheriffs alone are only 186 counties.
3. Run with `--follow` on the 52 `no_roster_found` sites to try common roster paths before
   classifying them as having no roster.

## First pass — catalog sample (superseded, kept for comparison)

Generated 2026-09-14, 132 candidates from the research catalogs. Retained because the contrast with
the national pass is the lesson: it looked like a vendor signal, but it was 69% FL+ID and therefore
told us about Florida and Idaho, not about the country.

| Access class | Count | % |
|---|---:|---:|
| `search_form` | 49 | 37.1% |
| `no_roster_found` | 18 | 13.6% |
| `html_roster` | 14 | 10.6% |
| `blocked` | 11 | 8.3% |
| `vendor_portal` | 9 | 6.8% |
| `unreachable` | 8 | 6.1% |
| `http_404` | 7 | 5.3% |
| `captcha_gated` | 6 | 4.5% |
| `robots_disallowed` | 5 | 3.8% |
| `pdf_roster` | 4 | 3.0% |
| `login_required` | 1 | 0.8% |

Vendor family: `smartweb` 4, `zuercher` 3, `socrata_open_data` 2.

**Buckets:** ingest candidates 76 (57.6%) · gated 23 (17.4%) · needs discovery 33 (25.0%).

## Data quality issues found in the input catalogs

Row labels that should be fixed upstream in `data/*.csv`:

- `FL Arrest report County`, `FL Booking reports County` — county name is a page title, not a county
- County column inconsistently carries the ` County` suffix and sometimes a facility name
- `data/us-jail-research-catalog.csv` mixes aggregator URLs into the same column as sheriff domains
  (58 rows, 32 unique SEO-spam hosts — now split out by `build_candidates.py`)

## Reproduce

```bash
cd /root/jailmap
./scripts/national/run.sh build_candidates.py
./scripts/national/run.sh fingerprint_sources.py \
    --input /src/data/national/candidates-national.csv --no-follow 2>/dev/null
./scripts/national/run.sh fingerprint_sources.py \
    --report /src/data/national/source-census.csv --by-state
```
