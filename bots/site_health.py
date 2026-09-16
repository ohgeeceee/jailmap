#!/usr/bin/env python3
"""jailmap-site-operator health check (Green tier: read-only).
Checks: container health, Postgres backup freshness, TLS cert expiry,
disk usage. Output = markdown digest to stdout. Never restarts, never
modifies anything. Cron appends into agent-queue/jailmap-ops-captain/.
"""
import os, ssl, subprocess, socket
from datetime import datetime, timezone
def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
def ts(path):
    try:
        age_h = (datetime.now().timestamp() - os.path.getmtime(path)) / 3600
        return age_h
    except OSError:
        return None
lines = [f"# Site operator health digest — {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", ""]
# 1. Containers
r = run("docker ps --format '{{.Names}}\\t{{.Status}}' | grep -E 'jailmap|postgres|meili|redis'")
lines += ["## Containers", "```", r.stdout.rstrip() or "(no jailmap containers found!)", "```", ""]
unhealthy = [l for l in r.stdout.splitlines() if "unhealthy" in l or "Restarting" in l]
for l in unhealthy:
    lines.insert(2, f"- **ALERT: {l}**")
# 2. Backup freshness (expect a DB backup newer than 26h)
lines += ["## Backups"]
found_backup = False
for root_dir in ("/root/jailmap/backups",):
    for dirpath, _dirs, files in os.walk(root_dir):
        for f in files:
            p = os.path.join(dirpath, f)
            age = ts(p)
            if age is not None and age < 26:
                found_backup = True
                lines.append(f"- OK: `{p}` ({age:.1f}h old)")
if not found_backup:
    lines.append("- **ALERT: no backup file newer than 26h found in /root/jailmap/backups**")
# 3. TLS expiry for jailmap.com
lines += [""]
try:
    ctx = ssl.create_default_context()
    with socket.create_connection(("jailmap.com", 443), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname="jailmap.com") as s:
            not_after = ssl.cert_time_to_seconds(s.getpeercert()["notAfter"])
            days = (not_after - datetime.now().timestamp()) / 86400
            flag = "OK" if days > 14 else "**ALERT: renew soon**"
            lines += ["## TLS", f"- jailmap.com cert: {days:.0f} days remaining — {flag}"]
except Exception as e:
    lines += ["## TLS", f"- **ALERT: TLS check failed: {e}**"]
# 4. Disk
r = run("df -h / /var/lib/docker 2>/dev/null | tail -n +2")
lines += ["", "## Disk", "```", r.stdout.rstrip(), "```", ""]
r2 = run("df --output=pcent / | tail -1 | tr -dc '0-9'")
if r2.stdout.strip() and int(r2.stdout.strip()) > 85:
    lines.insert(2, f"- **ALERT: root disk at {r2.stdout.strip()}%**")
print("\n".join(lines))
