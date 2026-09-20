# Ingest watchdog digest — 2026-09-17 10:15 UTC

## Alerts

## Latest run cycle (2026-09-17)
- 19 succeeded, 6 failed
- Committed: FL/Putnam (4), GA/Fulton (3016), GA/Fulton (3026), MT/Flathead (103), WY/Big Horn County (0), OH/Lorain County (100), MT/Yellowstone (656), MT/Ravalli (59), MT/Prairie (1), MT/Missoula (336), MT/Lewis and Clark (166), MT/Lake (22), MT/Jefferson (17), MT/Fergus (26), MT/Carter (143), MT/Beaverhead (17), ID/Power (14), ID/Cassia County (142), ID/Bonneville (336)
- Failures by error type:
  - WY ValueError x1: Laramie County
  - WV ValueError x1: Wirt County
  - MT JSONDecodeError x1: Gallatin
  - ID ConnectTimeout x1: Franklin
  - ID UniqueViolation x1: Cassia
  - MT HTTPStatusError x1: Garfield

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 657 / failed 1008
