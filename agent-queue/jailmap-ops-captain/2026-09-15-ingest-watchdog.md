# Ingest watchdog digest — 2026-09-15 10:15 UTC

## Alerts

## Latest run cycle (2026-09-15)
- 7 succeeded, 22 failed
- Committed: MT/Yellowstone (677), MT/Ravalli (58), MT/Missoula (327), MT/Jefferson (16), MT/Flathead (103), ID/Power (15), ID/Bonneville (332)
- Failures by error type:
  - MT JSONDecodeError x7: Silver Bow, Lewis and Clark, Glacier, Gallatin, Fergus, Custer, Chouteau
  - MT HTTPStatusError x6: Wheatland, Stillwater, Meagher, Madison, Garfield, Carbon
  - MT KeyError x4: Valley, Prairie, Lake, Carter
  - GA ValueError x2: Fulton, Fulton
  - MT ReadTimeout x1: Cascade
  - MT UnicodeDecodeError x1: Beaverhead
  - ID ConnectTimeout x1: Franklin

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 130 / failed 473
