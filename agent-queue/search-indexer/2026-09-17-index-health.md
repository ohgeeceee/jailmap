# search-indexer - index and outbox health

Generated 2026-09-17 12:20Z by `bots/`.

Green tier: read-only checks. It repairs nothing - index or hydration changes are production actions and wait for a human.

| Check | Result |
|---|---|
| Meilisearch /health | unreachable |
| Meilisearch indexes | unreachable |
| Outbox rows | 2366 |
| Newest outbox entry | 2026-09-17 12:10:08.79358+00 |
| Outbox rows stale vs source version | 0 |
| Public records | 5723 |

Interpretation: a rising stale count means published changes are not reaching search. The outbox is the contract between the records DB and the index; lag is a correctness bug, not a performance footnote.

## Next action

If stale rows are non-zero for two consecutive days, open a Red-tier draft: what is consuming the outbox, what stalled, and the exact command to drain it.
