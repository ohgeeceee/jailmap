# Florida SmartWeb Adapter — 2026-09-17

**Status:** Working — staging-only (4 records from Putnam County, FL in staging)

## What Was Built
- `backend/adapters/fl_smartweb.py` — One adapter covers **20+ Florida counties** using SmartWeb (CTS-America) vendor portal
- Pattern: `https://smartweb.<sheriff-domain>/smartwebclient/jail.aspx`
- Counties covered: Bradford, Escambia, Gadsden, Glades, Hamilton, Putnam, Sumter, Suwannee, and more

## Registration
- Added to `backend/ingest.py:56` (`from backend.adapters import fl_smartweb`)
- Registered as `fl_smartweb_staging` in `ADAPTERS` dict (staging-only default)
- Test jurisdiction inserted: FL / Putnam (id: `18460b93-3e11-4af3-ae61-557f3c39747f`)

## Egress Allowlist
Added 8 hosts to `SOURCE_ALLOWED_HOSTS`:
- 69.21.72.195, inmate.hamiltonsheriff.com, inmatelookup.myescambia.com
- portal.sumtercountysheriff.org, smartcop.suwanneesheriff.com
- smartweb.bradfordsheriff.org, smartweb.gladessheriff.org, smartweb.pcso.us

## Privacy
- **Mugshots:** SmartWeb URLs expire; adapter does NOT capture `mugshot_url` (returns `None`)
- All records marked `staging_only=True` — no public exposure without human review

## Next Steps
1. Add remaining FL counties (Flagler, Franklin, Gilchrist, Gulf, Highlands, Holmes, Jackson, Jefferson, Lafayette, Levy, Madison, Marion, Martin, Miami-Dade, Monroe, Nassau, Okaloosa, Okeechobee, Orange, Pasco, Pinellas, Polk, Putnam, Santa Rosa, Sarasota, Seminole, St. Johns, St. Lucie, Sumter, Suwannee, Taylor, Union, Volusia, Wakulla, Walton, Washington)
2. Test SmartWeb in other states (GA has SmartWeb counties too)
3. Promote FL Putnam to `staging_only=False` + `enabled=True` after review

## Verification
```bash
cd /root/jailmap && docker compose exec -T api python3 -m backend.ingest --state FL --county Putnam --dry-run
# → 4 validated records; dry run, no writes

cd /root/jailmap && docker compose exec -T api python3 -m backend.ingest --state FL --county Putnam
# → 4 validated records; staged privately
```
