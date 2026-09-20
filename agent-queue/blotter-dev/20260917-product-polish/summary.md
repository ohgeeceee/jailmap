# Product Polish Summary — 2026-09-17

## Changes

### Search endpoint — working
- Confirmed `GET /api/search?name=...` returns 200 + correct data (no fix needed)
- Frontend `SearchRecords.tsx` and backend `backend/api.py:search()` already agree on `name` param

### New: `/status` page (`src/app/status/page.tsx`)
- Reads `records.*` directly via Prisma server-side
- Shows: live jurisdictions count, bookings (48h + total), ingests in progress, 24h success/failure counts, top 5 errors (7 days)
- Health indicator: green/yellow/red based on run status
- Uses `.jm-theme` design tokens + stats-strip + admin-table patterns
- `BigInt()` constructors instead of `0n` literals (ES2020 target compatibility)
- `dynamic = 'force-dynamic'` prevents stale caching

### CSS additions
- `.status-page`, `.status-health`, `.ingestion-summary`, `.ingestion-metric`, `.status-note` in globals.css

## Verification

```
curl -sS http://127.0.0.1:3109/status -w "\nHTTP %{http_code}\n"     # 200
curl -sS http://127.0.0.1:3109/api/search?name=smith -w "\nHTTP %{http_code}\n"  # 200
curl -sS http://127.0.0.1:3109/ -w "\nHTTP %{http_code}\n"           # 200
curl -sS http://127.0.0.1:3109/leaderboard -w "\nHTTP %{http_code}\n" # 200
```

Leaderboard already existed at `src/app/leaderboard/page.tsx` + `LeaderboardClient.tsx` + `/api/leaderboard/route.ts`.

## Rollback
- Remove `src/app/status/page.tsx`
- Revert `src/app/globals.css` status-page block
- `docker compose build --no-cache web && docker compose up -d --no-deps web`
