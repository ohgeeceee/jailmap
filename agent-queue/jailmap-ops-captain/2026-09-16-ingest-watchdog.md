# Ingest watchdog digest — 2026-09-16 10:15 UTC

## Alerts

## Latest run cycle (2026-09-16)
- 10 succeeded, 14 failed
- Committed: MT/Prairie (8), MT/Lewis and Clark (165), MT/Lake (23), MT/Beaverhead (17), ID/Power (15), ID/Bonneville (334), MT/Ravalli (56), MT/Jefferson (17), SC/Laurens County (197), WY/Big Horn County (0)
- Failures by error type:
  - MT KeyError x3: Yellowstone, Missoula, Flathead
  - ID KeyError x2: Cassia County, Cassia
  - GA ValueError x2: Fulton, Fulton
  - OH KeyError x1: Lorain County
  - SD DatatypeMismatch x1: Lincoln County
  - IL DatatypeMismatch x1: Menard County
  - IA DatatypeMismatch x1: Marshall County
  - WY ValueError x1: Laramie County
  - WV ValueError x1: Wirt County
  - ID ConnectTimeout x1: Franklin

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 504 / failed 667
