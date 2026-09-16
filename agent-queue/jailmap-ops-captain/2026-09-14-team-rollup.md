# jailmap-ops-captain - team roll-up

Generated 2026-09-14 05:13Z by `install_team.py`.

Green tier: every line below comes from a read-only bot. Nothing in this run enabled a source, published a record, or left the machine.

| Bot | Result | Digest |
|---|---|---|
| source-scout-west | 426 uncovered counties in region | 2026-09-14-worklist.md |
| source-scout-south | 1393 uncovered counties in region | 2026-09-14-worklist.md |
| source-scout-north | 1300 uncovered counties in region | 2026-09-14-worklist.md |
| feed-builder | 42 orphaned adapters | 2026-09-14-adapter-audit.md |
| privacy-reviewer | BLOCKED 13, NEEDS_REVIEW 21, READY_FOR_ADAPTER 17 | clean: 5 | 2026-09-14-verdicts.md |
| search-indexer | 0 stale outbox rows | 2026-09-14-index-health.md |
| site-operator | digest written | 2026-09-14-site-health.md |

## Waiting on a human

- BLOCKED verdict rows: draft each disable with its reason, individually.
- Orphaned adapters: dry-run before registration.
- Scout worklists: a lead is evidence plus review, never a guessed hostname.
- Stale outbox rows: a correctness bug, not a performance footnote.
