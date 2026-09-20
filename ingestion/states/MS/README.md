# Mississippi ingestion

Canonical county list: counties.json. Current source status lives in PostgreSQL,
not in a guessed county endpoint or a template's ENABLED flag.

From /root/jailmap on the VPS:

```sh
python3 state_manager.py --list MS
python3 state_manager.py MS --dry-run
python3 state_manager.py MS
```

Use an exact --county name to narrow registered jurisdictions. A run with no
configured source says so explicitly; it does not report successful ingestion.
Verify facility, source, mapping, eligibility, timestamps and complete pagination
before enabling publication. See ingestion/README.md for the source workflow.
