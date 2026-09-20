# Ingest watchdog digest — 2026-09-18 10:15 UTC

## Alerts

## Latest run cycle (2026-09-18)
- 25 succeeded, 69 failed
- Committed: ID/Power (15), ID/Bonneville (330), GA/Fulton (2998), GA/Fulton (3018), WY/Big Horn County (0), TN/White (0), TN/Sumner (0), TN/Davidson (0), TN/Carter (249), OH/Lorain County (100), NY/Delaware (39), MT/Yellowstone (651), MT/Ravalli (60), MT/Prairie (1), MT/Missoula (336), MT/Lewis and Clark (166), MT/Lake (22), MT/Jefferson (19), MT/Flathead (103), MT/Fergus (25), MT/Carter (145), MT/Beaverhead (17), ID/Cassia County (142), FL/Putnam (10), CA/Fresno (0)
- Failures by error type:
  - CA ValueError x9: Ventura, Statewide, San Diego, San Bernardino, Sacramento, Orange, Kern, Contra Costa, Alameda
  - AR ValueError x6: Washington, Poinsett, Fulton, Faulkner, Cleburne, Carroll
  - NY ValueError x4: Westchester, Statewide, Oneida, New York City
  - NJ ValueError x4: Ocean, Middlesex, Hudson, Essex
  - VA ValueError x3: Virginia Beach, Roanoke, Henrico
  - TX ValueError x3: Travis, Tarrant, Harris
  - WI ValueError x2: Milwaukee, Dane
  - OK ValueError x2: Tulsa, Oklahoma
  - NM ValueError x2: Santa Fe, Bernalillo
  - ME ValueError x2: Penobscot, Kennebec
  - MA ValueError x2: Worcester, Plymouth
  - IN ValueError x2: Marion, Lake
  - CO ValueError x2: El Paso, Denver
  - AZ ValueError x2: Pima, Maricopa
  - ID UniqueViolation x1: Cassia
  - WA ValueError x1: King
  - UT ValueError x1: Salt Lake
  - TX KeyError x1: McLennan
  - TN ValueError x1: Knox
  - SC ValueError x1: Charleston
  - PA ValueError x1: Statewide
  - OR ValueError x1: Multnomah
  - OH ValueError x1: Cuyahoga
  - NH ValueError x1: Rockingham
  - NC ValueError x1: Cumberland
  - MT JSONDecodeError x1: Gallatin
  - MS ValueError x1: Hinds
  - MO ValueError x1: Jackson
  - MN ValueError x1: Statewide
  - MI ValueError x1: Wayne
  - KY ValueError x1: Fayette
  - KS ValueError x1: Sedgwick
  - IL ValueError x1: St. Clair
  - IL KeyError x1: Adams
  - ID ConnectTimeout x1: Franklin
  - IA ValueError x1: Polk
  - DE ValueError x1: Delaware County
  - CT KeyError x1: Hartford

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 769 / failed 1247
