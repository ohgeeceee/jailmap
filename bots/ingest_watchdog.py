#!/usr/bin/env python3
"""jailmap-ops-captain watchdog (Green tier: read-only).
Parses `roster_manager.py --status`, emits a markdown triage digest to
stdout. Cron redirects the digest into agent-queue/jailmap-ops-captain/.
Never writes to records.*, never enables sources, never ingests.
"""
import json, os, re, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
LIMIT = 400
STATE_FILE = "/tmp/jailmap_watchdog_state.json"
def main():
    out = subprocess.run(
        [sys.executable, "roster_manager.py", "--status", "--limit", str(LIMIT)],
        capture_output=True, text=True)
    lines = out.stdout.splitlines()
    runs, alltime = [], {}
    for line in lines:
        m = re.match(r"(failed|success):\s*(\d+)", line.strip())
        if m:
            alltime[m.group(1)] = int(m.group(2))
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 6 and parts[2] in ("success", "failed"):
            err = parts[6].strip() if len(parts) > 6 and parts[6].strip() else ""
            runs.append({"state": parts[0], "county": parts[1],
                         "status": parts[2], "recs": parts[3],
                         "started": parts[4], "error": err})
    now = datetime.now(timezone.utc)
    digest = [f"# Ingest watchdog digest — {now:%Y-%m-%d %H:%M} UTC", ""]
    stale = True
    if runs:
        newest = runs[0]["started"][:10]
        stale = newest != now.strftime("%Y-%m-%d")
    digest.append("## Alerts")
    if stale:
        digest.append("- **ALERT: no ingestion run recorded today** — check the 09:00 UTC cron / container.")
    if not runs:
        digest.append("- **ALERT: no runs parsed from --status** — pipeline may be broken.")
    digest.append("")
    last_cycle = [r for r in runs if runs and r["started"][:10] == runs[0]["started"][:10]] if runs else []
    ok = [r for r in last_cycle if r["status"] == "success"]
    bad = [r for r in last_cycle if r["status"] == "failed"]
    digest.append(f"## Latest run cycle ({runs[0]['started'][:10] if runs else 'n/a'})")
    digest.append(f"- {len(ok)} succeeded, {len(bad)} failed")
    if ok:
        digest.append("- Committed: " + ", ".join(f"{r['state']}/{r['county']} ({r['recs']})" for r in ok))
    if bad:
        by_err = Counter((r["state"], r["error"] or "unknown") for r in bad)
        digest.append("- Failures by error type:")
        for (st, err), n in by_err.most_common():
            counties = ", ".join(r["county"] for r in bad if r["state"] == st and (r["error"] or "unknown") == err)
            digest.append(f"  - {st} {err} x{n}: {counties}")
        digest.append("")
        digest.append("## Suggested next action (human decides)")
        digest.append("- Draft a fix under `agent-queue/` per MISSION.md; do not modify adapters directly.")
    digest.append("")
    if alltime:
        digest.append(f"## All-time: success {alltime.get('success','?')} / failed {alltime.get('failed','?')}")
    try:
        prev = json.load(open(STATE_FILE))
    except Exception:
        prev = None
    cur = {"last_fail": len(bad), "date": now.strftime("%Y-%m-%d")}
    json.dump(cur, open(STATE_FILE, "w"))
    if prev and prev.get("date") == cur["date"]:
        d = len(bad) - prev.get("last_fail", 0)
        if d > 0:
            digest.insert(2, f"- **REGRESSION: {d} more failures than the previous run today**")
        elif d < 0:
            digest.insert(2, f"- Improvement: {abs(d)} fewer failures than the previous run today")
    print("\n".join(digest))
if __name__ == "__main__":
    main()
