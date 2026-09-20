# search-indexer - index and outbox health

Generated 2026-09-19 12:20Z by `bots/`.

Green tier: read-only checks. It repairs nothing - index or hydration changes are production actions and wait for a human.

| Check | Result |
|---|---|
| Meilisearch /health | unreachable |
| Meilisearch indexes | unreachable |
| Outbox rows | 2949 |
| Newest outbox entry | 2026-09-19 12:17:14.173831+00 |
| Outbox rows stale vs source version | 0 |
| Public records | 5960 |

Interpretation: a rising stale count means published changes are not reaching search. The outbox is the contract between the records DB and the index; lag is a correctness bug, not a performance footnote.

## Next action

If stale rows are non-zero for two consecutive days, open a Red-tier draft: what is consuming the outbox, what stalled, and the exact command to drain it.
