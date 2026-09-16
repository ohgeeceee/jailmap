# Ingest watchdog digest — 2026-09-14 10:15 UTC

## Alerts

## Latest run cycle (2026-09-14)
- 9 succeeded, 20 failed
- Committed: MT/Yellowstone (687), MT/Ravalli (57), MT/Missoula (331), MT/Jefferson (17), MT/Flathead (106), ID/Power (15), ID/Bonneville (333), GA/Fulton (3022), GA/Fulton (3028)
- Failures by error type:
  - MT JSONDecodeError x7: Silver Bow, Lewis and Clark, Glacier, Gallatin, Fergus, Custer, Chouteau
  - MT HTTPStatusError x6: Wheatland, Stillwater, Meagher, Madison, Garfield, Carbon
  - MT KeyError x4: Valley, Prairie, Lake, Carter
  - MT ReadTimeout x1: Cascade
  - MT UnicodeDecodeError x1: Beaverhead
  - ID ConnectTimeout x1: Franklin

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 114 / failed 431
