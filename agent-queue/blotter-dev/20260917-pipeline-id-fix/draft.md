# Red-Tier Draft: Fix pipeline KeyError 'id' (434 of 988 weekly failures)

**Summary:** Fix the most-common ingestion failure — adapters produce `source_id` for charges/bonds but `backend/ingest.py:upsert()` read `.id`, raising KeyError on every public (non-staging) run for adapters that include charges or bonds.

**Files changed:**
- `backend/ingest.py` lines 102, 105: `charge['id']` → `charge['source_id']`, `bond['id']` → `bond['source_id']`
- `backend/adapters/mt_fergus.py` lines 81, 87, 97: same bug in adapter output (charges/bonds produced `id` instead of `source_id`)
- `backend/adapters/mt_carter.py` line 51: same bug in adapter output

**Reasoning:** The ingest upsert and normalize contract both use `source_id` as the child key. The `id` key was a legacy typo. All other adapters already use `source_id`. This fix should drop the 434 KeyError failures/week to near-zero.

**Rollback:** `cp backups/ingest.py.bak-20260917-090000 backend/ingest.py` + revert mt_fergus.py and mt_carter.py via git.

**Deploy:** `docker compose build --no-cache api && docker compose up -d --no-deps api`

**Verification:** After rebuild, `python -m roster_manager --run all` should show 0 KeyError failures.
