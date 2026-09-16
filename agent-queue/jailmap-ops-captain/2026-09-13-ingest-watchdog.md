# Ingest watchdog digest — 2026-09-13 18:21 UTC

## Alerts

## Latest run cycle (2026-09-13)
- 9 succeeded, 20 failed
- Committed: MT/Yellowstone (675), MT/Ravalli (57), MT/Missoula (330), MT/Jefferson (17), MT/Flathead (106), ID/Power (15), ID/Bonneville (342), GA/Fulton (3026), GA/Fulton (3038)
- Failures by error type:
  - MT JSONDecodeError x8: Silver Bow, Lewis and Clark, Gallatin, Fergus, Custer, Chouteau, Cascade, Carter
  - MT HTTPStatusError x7: Wheatland, Stillwater, Meagher, Madison, Glacier, Garfield, Carbon
  - MT KeyError x3: Valley, Prairie, Lake
  - MT UnicodeDecodeError x1: Beaverhead
  - ID ConnectTimeout x1: Franklin

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 105 / failed 411
