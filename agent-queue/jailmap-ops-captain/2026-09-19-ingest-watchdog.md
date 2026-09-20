# Ingest watchdog digest — 2026-09-19 10:15 UTC

## Alerts

## Latest run cycle (2026-09-19)
- 67 succeeded, 63 failed
- Committed: WY/Big Horn County (0), WY/Big Horn County (0), WA/Clark (0), VA/Virginia Beach (0), VA/Roanoke (0), UT/Salt Lake (0), UT/Iron County (0), TX/Travis (0), TX/Tarrant (0), TX/McLennan (0), TX/Harris (0), TN/White (0), TN/Sumner (0), TN/Knox (0), TN/Davidson (0), PA/Statewide (0), OH/Lorain County (100), OH/Logan County (0), OH/Cuyahoga (0), NY/Westchester (0), NY/Statewide (0), NY/Oneida (0), NY/New York City (0), NM/Santa Fe (0), NH/Rockingham (0), NE/Madison (0), ND/Stutsman (0), NC/Cumberland (0), MT/Yellowstone (654), MT/Prairie (3), MT/Missoula (328), MT/Lewis and Clark (168), MT/Lake (22), MT/Flathead (102), MT/Fergus (25), MT/Carter (149), MT/Beaverhead (17), MS/Lamar County (0), MO/Cedar County (0), ME/Penobscot (0), ME/Kennebec (0), MA/Worcester (0), MA/Plymouth (0), IN/Marion (0), IN/Lake (0), IL/St. Clair (0), ID/Power (15), ID/Bonneville (337), HI/Honolulu (0), GA/Fulton (3011), DE/Delaware County (0), CO/El Paso (0), CA/Ventura (0), CA/Tehama County (0), CA/Statewide (0), CA/San Bernardino (0), CA/Orange (0), CA/Kern (0), CA/Fresno (0), CA/Contra Costa (0), CA/Alameda (0), AZ/Pima (0), AZ/Maricopa (0), AR/Poinsett (0), AR/Faulkner (0), AR/Cleburne (0), AR/Carroll (0)
- Failures by error type:
  - OH ValueError x3: Miami County, Mercer County, Lake County
  - NJ HTTPStatusError x3: Middlesex, Hudson, Essex
  - WI HTTPStatusError x2: Milwaukee, Dane
  - SC HTTPStatusError x2: Charleston, Laurens County
  - OK ConnectError x2: Tulsa, Oklahoma
  - NJ ValueError x2: Ocean, Morris County
  - NC ValueError x2: Robeson County, Martin County
  - MO KeyError x2: Mercer County, Daviess County
  - ID UniqueViolation x2: Cassia County, Cassia
  - IA HTTPStatusError x2: Polk, Marshall County
  - WY ValueError x1: Laramie County
  - WV ValueError x1: Wirt County
  - WV ConnectError x1: Brooke County
  - WA ValueError x1: King County
  - WA HTTPStatusError x1: King
  - VA HTTPStatusError x1: Henrico
  - TX ValueError x1: Hays County
  - TN KeyError x1: Carter
  - OR HTTPStatusError x1: Multnomah
  - NY KeyError x1: Delaware
  - NM HTTPStatusError x1: Bernalillo
  - NH KeyError x1: Coos County
  - MT ValueError x1: Rosebud County
  - MS ConnectError x1: Hinds
  - MO ValueError x1: Jasper County
  - MO HTTPStatusError x1: Jackson
  - MN ConnectError x1: Statewide
  - MN ValueError x1: Marshall County
  - MI HTTPStatusError x1: Wayne
  - MI ValueError x1: Leelanau County
  - KY HTTPStatusError x1: Fayette
  - KS HTTPStatusError x1: Sedgwick
  - IL KeyError x1: Adams
  - ID ConnectTimeout x1: Franklin
  - IA ValueError x1: Woodbury County
  - GA KeyError x1: Gilmer County
  - GA ValueError x1: Fulton
  - FL KeyError x1: Putnam
  - DE KeyError x1: Kent County
  - CT KeyError x1: Hartford
  - CO HTTPStatusError x1: Denver
  - CO KeyError x1: Delta County
  - CA HTTPStatusError x1: San Diego
  - CA ConnectError x1: Sacramento
  - CA ValueError x1: Alpine County
  - AR ValueError x1: Washington
  - AR ConnectTimeout x1: Fulton
  - AL ValueError x1: Winston County
  - SD HTTPStatusError x1: Lincoln County
  - IL HTTPStatusError x1: Menard County
  - GA HTTPStatusError x1: Floyd County

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 1316 / failed 3623
