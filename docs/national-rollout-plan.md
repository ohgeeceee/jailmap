# JailMap — National Roster Rollout, Week 1

Written 2026-09-14. Read `MISSION.md` first — its Green/Yellow/Red tiers govern everything here.

---

## 1. The honest baseline

Measured from the live database and filesystem, not estimated.

| What | Count |
|---|---|
| Counties in national directory | 3,143 |
| Jails in directory | 3,531 |
| Jails with a real jurisdiction website | **7** |
| Jails whose "website" is a Census TIGERweb geometry query | 3,528 |
| Registered ingestion jurisdictions | 51 |
| Enabled for ingestion | 27 |
| Produced a successful run in the last 7 days | **9** |
| Counties with any registered source | 43 |
| Roster sources in `data/official-jail-source-leads.csv` | 7 |
| `adapter.py` files under `states/` | 2,978 |
| …that raise `NotImplementedError` | **2,947 (99.0%)** |
| …with real working code | 31 |
| Real adapters in `backend/adapters/` | 40 files, **11 registered** |
| Hosts in the `SOURCE_ALLOWED_HOSTS` egress allowlist | ~40 (Montana-dominated) |
| Booking records in the database | 4,879 (4,617 public) |

**Coverage today: 9 of 3,531 jails actively ingesting — 0.25%.**

Two things must be said plainly, because they reshape the whole plan:

**The national directory is not a source registry.** All 3,528 TIGERweb rows carry the same
verification note: *"Census local-jail landmark… Directory listing only: operational and roster
availability require source review."* They are geographic points on a map. Not one has a roster URL.

**The 2,978 adapter files are scaffolding, not coverage.** Counting them as progress is the
single biggest risk in this project. Any dashboard that reports "2,978 counties set up" is lying.
Fixing that lie is Day 1.

---

## 1b. Findings from building the Day 1–2 tools

These came out of running the tools against live data, not from reading the schema. Each one
would have silently corrupted the rollout if discovered a week later.

| Finding | Why it matters |
|---|---|
| `"Jail"."isActive"` is **true for only 7 of 3,531 rows** — exactly the 7 with real websites | Any query filtering on `isActive` silently collapses "national" to 7 jails. The first build of the census tool did exactly this. Filter on it only deliberately. |
| **Guessing domains fails.** A 6-jail live sample produced 5 `ConnectError`s | `<county>countysheriff.com` almost never resolves. Discovery must consume a real candidate list (`--input`), not invented hostnames. |
| **`robots.txt` is a live per-source gate.** `ravalli-so-mt.zuercherportal.com` disallows our bot while `gallatin-so-mt.zuercherportal.com` allows it | One vendor tenant can be off-limits while the same vendor elsewhere is fine. Robots compliance must be per-origin, not per-vendor. |
| **Vendor detection must match host first, body second.** | Body-first matching produced `appriss_vine` on a Hawaii corrections page and `tyler_odyssey` on a Socrata portal — both false. Corrections pages routinely *mention* systems they don't run (VINE notification, marketing links). |
| Every national `facility_sources` row points at `tigerweb.geo.census.gov` | There is no national source registry. It has to be built, and that is most of Week 1. |

**Validated:** given a real candidate list, the census classifies correctly — Zuercher →
`vendor_portal (zuercher)`, Fulton's Socrata portal → `vendor_portal (socrata_open_data)`,
Osceola → `search_form`, Johnson County KS → `html_roster`.

---

## 2. The thesis: do not write 3,531 scrapers

Three facts decide the strategy.

**Fact 1 — Jails buy software from a small number of vendors.** A Zuercher portal is the same
Zuercher portal whether it serves Ravalli County MT or Clackamas County OR. One well-built
adapter can cover hundreds of jails. This is the only path that reaches national scale.

**Fact 2 — Most jails do not publish a machine-readable roster.** Some publish a PDF, many publish
nothing at all, some sit behind captcha or a login. Those are access problems, not engineering
problems. No amount of code solves them, and `MISSION.md` forbids bypassing any of it.

**Fact 3 — The bottleneck is source discovery and your review time, not parsing.** Parsing is the
cheap part. Finding the real roster URL for 3,531 jails, and deciding which are legitimate to
ingest, is the work.

### Leverage, in order

| Priority | Work | Why |
|---|---|---|
| **A** | Vendor-family adapters | One adapter → tens or hundreds of jails |
| **B** | Source discovery at directory scale | Turns 3,531 landmarks into candidate URLs |
| **C** | Authorization + review throughput | Your time; the gate that actually limits growth |

### Realistic Week-1 target

Not 3,531. **Not even close**, and pretending otherwise wastes the week.

- 400–800 jails' sources identified and classified (reachable / gated / no roster published)
- 3–5 vendor families with working, tested adapters
- 100–200 jails actually ingesting
- A repeatable weekly loop that keeps growing without you babysitting it

Going from 9 to ~150 working jails in a week is a 16× jump. That is the honest goal.

---

## 3. The week

Each day has one objective, prompts to hand to the agent, scripts to run, and a hard exit
criterion. **Do not roll into the next day with the previous day's exit criterion unmet** — that
is how the stub illusion got built in the first place.

Red-tier actions (per `MISSION.md`) are marked. Those are drafted into
`agent-queue/jailmap-ops-captain/<date>-<name>/` and wait for your explicit approval.

---

### Day 1 — See the truth, stop the bleeding

**Objective:** know the real coverage number, and make the two broken ingestion services stop
reporting success they don't have.

**Prompts**

> Audit JailMap's real national coverage. Query `records.jurisdictions`, `records.ingestion_runs`,
> and `records.inmates`, and count the `adapter.py` files under `states/` that contain
> `NotImplementedError`. Report as three numbers: jails with a real roster source, jurisdictions
> enabled, and jurisdictions that produced a successful run in the last 7 days. Do not count
> scaffolding as coverage. Write the result to `docs/coverage-baseline.md`.

> `jailmap-ingest.service` exits 1 and `jailmap-wa-ingest.service` fails 11/11. Triage both from
> the journal. For WA, confirm whether the hostnames still resolve before touching any code.
> Propose fixes as a draft in `agent-queue/jailmap-ops-captain/`; do not restart or change
> services without approval.

**Scripts**

```bash
cd /root/jailmap
python3 scripts/national/audit_coverage.py --markdown   # the honest number
systemctl status jailmap-ingest.service --no-pager | tail -20
journalctl -u jailmap-wa-ingest -n 60 --no-pager
```

**Exit criterion:** `docs/coverage-baseline.md` exists with a number you trust, and both failing
services are either fixed or explicitly written off with a reason.

---

### Day 2 — Fingerprint the national directory

**Objective:** turn 3,531 anonymous landmarks into a classified source census. This is the day
that unblocks everything else.

**Do not guess hostnames.** A live 6-jail sample proved it: 5 of 6 guessed domains returned
`ConnectError`. `<county>countysheriff.com` almost never resolves. Feed the census a real
candidate list instead. There are two sources, and the second one is the unlock.

**Source 1 — the existing research catalogs** (small, already assembled):

```bash
./scripts/national/run.sh build_candidates.py
```

Reads `data/us-jail-research-catalog.csv`, `data/official-sources-only.csv`,
`data/al-research-catalog.csv`, `data/fl-county-roster-urls.csv`, `data/idaho-jail-sources.csv`,
`data/sd-jail-sources.csv`, normalises them to `state,county,jail,url`, deduplicates, and splits
three ways:

| Output | What it is |
|---|---|
| `candidates-national.csv` | official + unknown hosts, ready to probe |
| `candidates-thirdparty.csv` | aggregator mirrors, **never probed** |
| `candidates-backlog.csv` | rows with no URL — the discovery backlog |

Current yield: **123 probe candidates, 58 third-party URLs excluded, 111 backlog rows.**

The exclusion step matters. The catalogs mix aggregator URLs into the same column as real sheriff
domains. Fed through unfiltered, the census would produce a vendor histogram built partly on
mirrors — and `MISSION.md` is explicit that a third-party mirror is never an authority. The 58
excluded are 32 unique SEO-spam hosts dressed up as county jails:

```
alaskaprisonroster.org          pimacountyjailaz.org       navajocountyjailaz.org
kenaipeninsulacountyjail.org    yavapaicountyjailaz.org    coconinocountyjailaz.org
```

Official Pima County is `pimasheriff.org`. These are not sources; they are competitors.

**Source 2 — the CISA `.gov` registry (the scale unlock).** ~326 catalog rows cannot reach 3,531
jails. But `.gov` domains are an authoritative public registry, so counties can be mapped to their
real government domain without guessing:

```bash
curl -o data/national/dotgov-full.csv \
  https://raw.githubusercontent.com/cisagov/dotgov-data/main/current-full.csv
```

16,669 rows: domain, organization name, city, state. Joined against `"County"`:

| Result | Count |
|---|---|
| Counties matched to ≥1 official `.gov` domain (registered) | 2,223 / 3,143 (70.7%) |
| **Counties with ≥1 domain that actually resolves** | **1,990 / 3,143 (63.3%)** |
| Candidate domains emitted (max 2/county) | 3,183 |
| …that resolve (535 are NXDOMAIN) | **2,648** |
| …with a dedicated sheriff / sheriff's-office domain | 270 registered → **186 resolving** |
| Ambiguous matches held for review | 1,011 |

**The registry proves ownership, not liveness.** That 70.7% is how many counties *own* a `.gov`
domain; only 63.3% have one that answers. Of 270 sheriff domains, 84 (31%) are NXDOMAIN —
1,990 is the honest reachable ceiling from this source.

This was verified, not assumed. The first national census pass returned **41.9% unreachable**, which
looked like a broken tool. It was not: `dig @1.1.1.1` and the system resolver agreed on every
NXDOMAIN, so the domains genuinely do not resolve. Agencies register a domain defensively and
deploy a site years later. Use `--dns-check` to filter before spending probe requests:

```bash
./scripts/national/run.sh build_candidates.py --dns-check
```

Sheriff domains are the high-value targets — `calhounalsheriff.gov`, `chiltoncountyso.gov`,
`leecosheriffal.gov`, `bencosoar.gov`. A sheriff's own domain is far more likely to expose a roster
than a commission homepage.

### Three precision rules learned the hard way

Getting this join wrong produces *wrong sources*, which is worse than missing ones — a wrong
source silently attaches another county's roster to the wrong place. Three real false positives
encountered while building it:

1. **Org-name substring matching.** `leesheriffar.gov` (organization "Lee County Arkansas
   Sheriff") was assigned to **Arkansas County**. Fix: parse the county out of the org name by
   taking the words before the first `County`, and require equality — that yields `lee`, not
   `arkansas`.
2. **Loose domain suffix matching.** `endswith`/contains matched `18wjdarkansas.gov` (18th West
   Judicial District) and `almaarkansas.gov` (City of Alma) to Arkansas County. Fix: accept only
   exact matches, county-name *prefixes*, and explicit `countyof`/`cityof` prefixes.
3. **County named after its own state.** After fixing 1 and 2, Arkansas County still matched
   `arkansas.gov` and `arkansas529.gov` — the *state* sites. Fix: when `county_slug ==
   state_slug` (Arkansas, Washington, Nevada, Mississippi, …), skip domain matching entirely and
   require an organization that literally reads `<Name> County`.

With all three applied, Arkansas County resolves to `arkansascountyar.gov` (org: "Arkansas
County") — correct — and the 65 remaining state-named counties look sane. Matches went **up** as
precision improved, because counties fell through to the reliable org path instead of matching
garbage.

**Prompts**

> Extend `build_candidates.py` with a `.gov` registry source. Join
> `data/national/dotgov-full.csv` against `"County"` and emit `candidates-dotgov.csv` with
> `state,county,jail,url`. Match on the domain first and the organization name second, and require
> the county name to appear as a distinct token so `leesheriffar.gov` is not assigned to Arkansas
> County. Rank sheriff/`so` domains above commission domains. Report the match rate and list every
> match that is ambiguous for review.

> Run the census against the sheriff-domain subset first — roughly 267 counties, the highest
> expected yield — before spending requests on commission homepages.

**Scripts**

```bash
cd /root/jailmap

# 1. Build the probe list from the research catalogs (separates out 3rd-party mirrors)
./scripts/national/run.sh build_candidates.py

# 2. Census from the catalog list
./scripts/national/run.sh fingerprint_sources.py \
    --input /src/data/national/candidates-national.csv --no-follow 2>/dev/null

# 3. Census that also tries common roster paths on sites that load (+6 req/host)
./scripts/national/run.sh fingerprint_sources.py --input /src/data/national/candidates-national.csv

# 4. Vendor-family histogram — this decides Day 3
./scripts/national/run.sh fingerprint_sources.py --report /src/data/national/source-census.csv --by-state

# 5. Eyeball targets first, no network traffic at all
./scripts/national/run.sh fingerprint_sources.py --sample 20 --states 5 --dry-run
```

**Exit criterion:** `source-census.csv` has ≥200 jails classified, the vendor histogram names the
top three families to build, and `candidates-dotgov.csv` exists with ~2,000 counties at a reviewed
precision.

---

### Day 3 — One vendor family, built properly

**Objective:** turn the top vendor family into a working adapter that covers many jails at once.

**Prompts**

> Build a `<vendor>` family adapter under `backend/adapters/`. It must take a jurisdiction with a
> vendor portal URL and return the standard normalized record contract used by
> `backend/ingest.py`. Enforce bounded fetch / timeout / response-size, reject duplicate booking
> keys, exclude juvenile and sealed records, and preserve existing suppressions. Register it in
> the `ADAPTERS` dict. Do not set `enabled=true` or `staging_only=false` — draft it staging-only
> with tests and a dry-run transcript.

> `backend/adapters/` has 40 adapter files but only 11 are registered in `backend/ingest.py`.
> List which real adapters are not wired up, and for each say whether it still targets a live
> source. Propose a registration diff for the ones that do.

**Scripts**

```bash
# wire the 29 orphaned adapters that still work — cheap win, no new code
python3 scripts/national/audit_adapters.py --unregistered

# dry-run one vendor family across every jurisdiction using it
python3 scripts/national/vendor_dryrun.py --vendor zuercher --limit 25
```

**Exit criterion:** one vendor family ingests staging-only from ≥10 jurisdictions in a dry run
with zero unhandled exceptions, and every previously-orphaned working adapter is either
registered or deleted.

---

### Day 4 — Source discovery for the long tail

**Objective:** handle the jails with no vendor portal and no obvious site — the majority.

**Prompts**

> The vendor census is done. For jails with `no_roster_published` or `search_form`, do a bounded
> discovery pass: sheriff site → "inmate"/"roster"/"booking"/"custody" pages → any linked
> PDF/JSON/table. Respect `robots.txt` and never attempt a captcha or login. Record
> evidence (the page that links to the roster) for every candidate URL. Write results to
> `data/official-jail-source-leads.csv` in the existing schema, `publication_default` set to
> `staging_only` or `blocked` — never a public value.

> Report which states have the highest concentration of *reachable* sources versus *gated* ones.
> That tells Jon where the review hours buy the most coverage.

**Scripts**

```bash
python3 scripts/national/discover_rosters.py --input data/source-census.csv --out data/official-jail-source-leads.csv
python3 scripts/national/fingerprint_sources.py --report data/source-census.csv --by-state
```

**Exit criterion:** `official-jail-source-leads.csv` grown from 7 rows to ≥300, each with an
evidence URL and a `publication_default` that is never public.

---

### Day 5 — Make approved sources actually able to ingest

**Objective:** remove the last gate between a reviewed source and live records.

This is a real blocker today: `backend/ingest.py`'s `standard_json` refuses any host not in
`SOURCE_ALLOWED_HOSTS`, and that list is 40 Montana-dominated entries. Discovery is worthless if
approved sources can't be fetched.

**Prompts**

> Design the authorization workflow: a reviewed source in `records.jurisdictions` with
> `review_status='verified'` and a real `authorization_reference` should be able to ingest without
> a manual `.env` edit per host. Propose the smallest safe change — either a per-jurisdiction
> allowed-host column enforced at fetch time, or a generated allowlist derived from verified
> jurisdictions. Show the failure mode being prevented (SSRF, DNS rebinding, user-supplied
> endpoints). Draft it; do not deploy.

**Scripts**

```bash
python3 scripts/national/render_allowed_hosts.py --from-db          # proposed allowlist
python3 scripts/national/render_allowed_hosts.py --from-db --diff    # vs .env
```

**Exit criterion:** a reviewed, approved plan for host authorization (drafted, not deployed), so
that adding a source is a review action and not a production `.env` edit.

---

### Day 6 — Automate the loop

**Objective:** make growth continuous instead of a series of heroic days.

**Prompts**

> Wire a daily operations loop: one systemd timer that runs ingestion for all enabled
> jurisdictions, one that probes source health and writes a machine-readable report, and one that
> refreshes the coverage census. Escalate to Jon only for the `MISSION.md` real-time triggers
> (site down >15 min, disk >90%, a source enabled or published without approval). Everything else
> goes in the 07:00 MT digest. Draft all units; do not enable them.

> Build failure triage: group failed `records.ingestion_runs` by `error_type` and jurisdiction,
> and for each cluster state whether it is a source-side change, an adapter bug, or a dead
> hostname. Output a ranked fix list, not a wall of log lines.

**Scripts**

```bash
python3 scripts/national/ops_report.py --json > /var/log/jailmap/ops-$(date +%F).json
python3 scripts/national/ops_report.py            # human digest, one screen
python3 scripts/national/triage_failures.py       # ranked fix list
```

**Exit criterion:** the loop runs unattended for 24h and the digest is one screen with a real
number at the top and a ranked fix list under it.

---

### Day 7 — Review, decide, and set Week 2

**Prompts**

> Produce the Week-1 review: coverage at start and end, jails added, vendor families built,
> sources classified, and the true cost per new jurisdiction (review minutes vs. machine time).
> Name the single biggest remaining blocker. Then propose Week 2 with the same day-by-day
> structure, aimed at whichever of the three leverage tiers is now the binding constraint.

**Exit criterion:** you know your real growth rate per week, and you know what the *next*
bottleneck is. That is what makes this a system instead of a sprint.

---

## 4. What this plan deliberately does not do

- **No bypassing captcha, login, paywalls, or `robots.txt`.** `MISSION.md` forbids it, and it is
  the fastest way to lose the entire project's legitimacy. Gated jails get recorded as `gated` and
  approached by outreach, not by evasion.
- **No third-party mirrors as authority.** Vendor portals are used only when they are the
  official platform the county itself links to.
- **No auto-enabling anything.** Every source stays `staging_only` until you approve it. The
  Red-tier list in `MISSION.md` is not advisory.
- **No claiming the 2,978 scaffold files as progress.** They are 2,947 `NotImplementedError`
  stubs. The correct number for today is 9 jails ingesting.
- **No single mega-script.** Each day is independently verifiable, because the failure mode here
  is a pipeline that looks like it works.

---

## 5. Standing command reference

```bash
cd /root/jailmap

# Tools run inside the api container (it holds DATABASE_URL + psycopg).
# /root/jailmap is mode 0700, so run.sh mounts the needed subtrees individually.
# Container banner goes to stderr — use 2>/dev/null when piping.

# Coverage truth
./scripts/national/run.sh audit_coverage.py                  # human table
./scripts/national/run.sh audit_coverage.py --markdown 2>/dev/null > docs/coverage-baseline.md
./scripts/national/run.sh audit_coverage.py --json 2>/dev/null   # machine-readable

# Directory census + vendor ranking
./scripts/national/run.sh fingerprint_sources.py --sample 20 --states 5 --dry-run   # no network
./scripts/national/run.sh fingerprint_sources.py --input /src/data/national/candidates-known.csv
./scripts/national/run.sh fingerprint_sources.py --report /src/data/national/source-census.csv --by-state

# Existing ingestion, unchanged
./scripts/state-ingest.sh MT --dry-run
./scripts/coverage.sh --state MT
docker compose exec -T api python -m backend.ingest --state MT
```

**Politeness invariants** baked into `fingerprint_sources.py` — do not weaken them:
`robots.txt` obeyed per-origin, 1 request/second/host, 12s timeout, 400 KB response cap,
captcha and login pages recorded and abandoned, `--dry-run` for zero network traffic.

`--concurrency N` parallelises **across hosts only**. The 1-req/sec-per-host limit is enforced
exactly by reserving each host's next allowed slot under a lock, so N workers on the same host
still produce one request per second while workers on different hosts never block each other.
Verified: an 8-worker run on the 9-candidate test list returns byte-identical classifications to
the sequential run. Runs are resumable — re-running skips any `(state, county, jail)` already
present in the output file, so an interrupted 2,600-job crawl continues rather than restarting.

Scale of a full national pass: ~2,648 resolving domains, roughly 2 requests each (robots.txt plus
the page). Sequential that is hours; at `--concurrency 12` it is tens of minutes. Nothing is sent
faster than one request per second to any single site.

Admin visibility for all of this is already live at `/admin?tab=coverage`, `?tab=ingestion`, and
`?tab=pipeline` on jailmap.com.
