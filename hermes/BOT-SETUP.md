# JailMap bot team - installation and operation

Installed by `install_team.py`. Read `MISSION.md` first: the Green/Yellow/Red tiers
govern every bot here. This file records what was installed, how each bot behaves,
and what still requires a human.

## What was installed

| Path | Purpose |
|---|---|
| `bots/jailmap_bots.py` | shared read-only helpers (psql SELECTs, digest writer) |
| `bots/scout_region.py` | source-scout-{west,south,north}: uncovered-county worklists |
| `bots/adapter_audit.py` | feed-builder: adapter registration audit, orphaned candidates |
| `bots/privacy_verdicts.py` | privacy-reviewer: a verdict per registered source |
| `bots/index_health.py` | search-indexer: Meilisearch + outbox lag |
| `/etc/cron.d/jailmap-bot-team` | the six schedules (UTC) |
| `agent-queue/<bot>/` | one digest directory per bot |

`site-operator` continues to use the pre-existing `bots/site_health.py`; the
installer now writes its output into `agent-queue/site-operator/`.

## Green-tier guarantee

Every bot in this team is read-only against production:

- all database access is a `SELECT`, run through
  `docker exec jailmap-postgres-1 psql`;
- the only files written are digests under `agent-queue/<bot>/`;
- no bot enables a jurisdiction, flips `staging_only`, publishes a record, starts a
  fetch, sends mail, or restarts a service.

A digest that says nothing is a failure signal, not a quiet day. Silence is treated
as breakage.

## Running a bot by hand

```sh
cd /root/jailmap
python3 bots/scout_region.py north --limit 60 --write
python3 bots/adapter_audit.py --write
python3 bots/privacy_verdicts.py --write
python3 bots/index_health.py --write
```

Without `--write` each bot prints its digest to stdout and touches nothing, which is
the way to inspect a change in behaviour before letting cron run it.

## Reading the output

- `scout_region.py` ranks counties with no enabled source by facility count, and
  marks which already carry a lead. It deliberately does not invent hostnames:
  the rollout plan measured that `<county>countysheriff.com` almost never resolves.
- `adapter_audit.py` separates real adapter modules from `NotImplementedError`
  scaffolding. The scaffolding must never be reported as coverage - 2,947 of 2,978
  state adapter files are scaffolding, per `docs/coverage-baseline.md`.
- `privacy_verdicts.py` applies the MISSION.md checklist mechanically and reports
  how many enabled sources carry a clean verdict. When that number is below the
  enabled count, "enabled" overstates the product.
- `index_health.py` treats outbox lag as a correctness bug: published changes that
  never reach search are not a performance footnote.

## Still the human's decision

- enabling any jurisdiction, or flipping `staging_only`;
- publishing a record, or sending any outbound email;
- editing application code, restarting services, or changing Docker/nginx/DNS;
- acting on any BLOCKED verdict - disable these one at a time, with a recorded
  reason, never as a silent batch.

## Rollback

```sh
rm -f /etc/cron.d/jailmap-bot-team
rm -f /root/jailmap/bots/{scout_region,adapter_audit,privacy_verdicts,index_health}.py
```

Digests already written stay in `agent-queue/` as the audit trail.
