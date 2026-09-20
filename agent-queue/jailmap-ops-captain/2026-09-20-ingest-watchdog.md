# Ingest watchdog digest — 2026-09-20 10:15 UTC

## Alerts

## Latest run cycle (2026-09-20)
- 91 succeeded, 36 failed
- Committed: NJ/Ocean (2), WY/Big Horn County (0), WY/Big Horn County (0), WA/King County (2), TX/McLennan (0), TN/Sumner (0), TN/Davidson (0), TN/Carter (246), OH/Miami County (3), OH/Lorain County (100), NY/Delaware (40), NC/Robeson County (7), NC/Martin County (5), MT/Yellowstone (664), MT/Prairie (10), MT/Missoula (334), MT/Lewis and Clark (168), MT/Lake (21), MT/Flathead (100), MT/Fergus (25), MT/Carter (154), MT/Beaverhead (17), MI/Leelanau County (22), ID/Power (15), ID/Cassia County (142), ID/Bonneville (340), IA/Woodbury County (10), GA/Fulton (3011), FL/Putnam (2), DE/Kent County (1), CA/Tehama County (0), CA/Fresno (0), AL/Winston County (11), AR/Poinsett (100), AR/Carroll (81), WV/Wirt County (38), WA/Clark (0), VA/Virginia Beach (0), VA/Roanoke (0), UT/Salt Lake (0), UT/Iron County (0), TX/Travis (0), TX/Tarrant (0), TX/Harris (0), TN/Knox (0), PA/Statewide (0), OH/Mercer County (63), OH/Logan County (0), OH/Lake County (3), OH/Cuyahoga (0), NY/Westchester (0), NY/Statewide (0), NY/Oneida (0), NY/New York City (0), NM/Santa Fe (0), NJ/Morris County (88), NH/Rockingham (0), NH/Coos County (1), NE/Madison (0), ND/Stutsman (0), NC/Cumberland (0), MT/Rosebud County (5), MS/Lamar County (0), MO/Mercer County (1), MO/Jasper County (28), MO/Daviess County (1), MO/Cedar County (0), MN/Marshall County (4), ME/Penobscot (0), ME/Kennebec (0), MA/Worcester (0), MA/Plymouth (0), IN/Marion (0), IN/Lake (0), IL/St. Clair (0), HI/Honolulu (0), GA/Gilmer County (1), DE/Delaware County (0), CO/El Paso (0), CA/Ventura (0), CA/Statewide (0), CA/San Bernardino (0), CA/Orange (0), CA/Kern (0), CA/Contra Costa (0), CA/Alpine County (2), CA/Alameda (0), AZ/Pima (0), AZ/Maricopa (0), AR/Faulkner (0), AR/Cleburne (0)
- Failures by error type:
  - NJ HTTPStatusError x3: Middlesex, Hudson, Essex
  - SC HTTPStatusError x2: Laurens County, Charleston
  - OK ConnectError x2: Tulsa, Oklahoma
  - WI HTTPStatusError x2: Milwaukee, Dane
  - IA HTTPStatusError x2: Polk, Marshall County
  - ID ConnectTimeout x1: Franklin
  - GA HTTPStatusError x1: Floyd County
  - WV ConnectError x1: Brooke County
  - MS ConnectError x1: Hinds
  - MN ConnectError x1: Statewide
  - CA ConnectError x1: Sacramento
  - AR ValueError x1: Washington
  - AR ConnectTimeout x1: Fulton
  - VA HTTPStatusError x1: Henrico
  - TN HTTPStatusError x1: White
  - OR HTTPStatusError x1: Multnomah
  - NM HTTPStatusError x1: Bernalillo
  - MO HTTPStatusError x1: Jackson
  - MI HTTPStatusError x1: Wayne
  - KY HTTPStatusError x1: Fayette
  - KS HTTPStatusError x1: Sedgwick
  - WY ValueError x1: Laramie County
  - WA HTTPStatusError x1: King
  - TX ValueError x1: Hays County
  - SD HTTPStatusError x1: Lincoln County
  - IL HTTPStatusError x1: Menard County
  - ID UniqueViolation x1: Cassia
  - GA ValueError x1: Fulton
  - CO HTTPStatusError x1: Denver
  - CA HTTPStatusError x1: San Diego

## Suggested next action (human decides)
- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.

## All-time: success 2259 / failed 4640
