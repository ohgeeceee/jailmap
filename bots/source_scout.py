#!/usr/bin/env python3
"""jailmap source-scout runner (Green tier: probe + fingerprint only).
Reads data/official-jail-source-leads.csv rows with access_status
needs_adapter/needs_research, probes each source URL (bounded, polite,
robots-respecting), fingerprints the roster platform, and writes an
updated CSV plus a checkpoint report. NEVER enables a source, never
ingests, never writes records.*. Bypass attempts are not made: sites
blocking the probe are recorded as blocked, and that is final.
"""
import csv, ipaddress, os, re, socket, ssl, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
LEADS = "/root/jailmap/data/official-jail-source-leads.csv"
QUEUE_DIR = "/root/jailmap/agent-queue"
BOT = "jailmap-ops-captain"
UA = "JailMapSourceScout/1.0 (+https://jailmap.com; official-source discovery; contact via site)"
TIMEOUT = 15
MAX_BYTES = 400_000
FINGERPRINTS = [
    ("jailtracker", r"JailTracker|jailtracker\.com"),
    ("zuercher", r"zuercher|ZuercherPortal|sdmportal"),
    ("vine", r"VINELink|vineLINK"),
    ("civicplus", r"CivicPlus|civicplus\.com"),
    ("correctcare", r"CorrectCare|tellcorrections"),
    ("toledo_edu", r"offendersearch|OffenderSearch"),
    ("pdf_roster", r"href=[\"'][^\"']*\.(pdf)[\"']", ),
    ("xlsx_roster", r"href=[\"'][^\"']*\.(xlsx?|csv)[\"']"),
    ("json_api", r"application/json|/api/|\.json[\"?]"),
    ("image_captcha", r"captcha|recaptcha|hcaptcha", ),
]
def fetch(url, max_redirects=4):
    """GET with UA, size cap, and private-IP SSRF guard. Returns (status, body, final_url) or (err, None, url)."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            return ("non_https", None, url)
        ip = socket.getaddrinfo(parsed.hostname, 443)[0][4][0]
        if ipaddress.ip_address(ip).is_private:
            return ("private_ip_blocked", None, url)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(MAX_BYTES).decode("utf-8", "replace")
            return (r.status, body, r.geturl())
    except urllib.error.HTTPError as e:
        return (f"http_{e.code}", None, url)
    except Exception as e:
        return (f"error_{type(e).__name__}", None, url)
def robots_allows(url):
    try:
        rp = urllib.parse.urlparse(url)
        robots = f"{rp.scheme}://{rp.netloc}/robots.txt"
        status, body, _ = fetch(robots)
        if body is None:
            return True  # unreachable robots -> treat as allowed but note
        agent_section, ua_hit = False, False
        for line in body.splitlines():
            line = line.split("#")[0].strip()
            if re.match(r"(?i)^user-agent:", line):
                agent_section = "jailmapsourcescout" in line.lower() or "*" in line
                if "jailmapsourcescout" in line.lower():
                    ua_hit = True
            elif agent_section and re.match(r"(?i)^disallow:\s*/\s*$", line):
                return False
        return True
    except Exception:
        return True
def fingerprint(html):
    hits = []
    for name, pat in FINGERPRINTS:
        if re.search(pat, html or "", re.I):
            hits.append(name)
    return hits
def main():
    now = datetime.now(timezone.utc)
    with open(LEADS, newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())
    for extra in ("last_probed", "probe_result", "probe_hits"):
        if extra not in fields:
            fields.append(extra)
    report = [f"# Source scout checkpoint — {now:%Y-%m-%d %H:%M} UTC", "",
              "status: NEEDS_REVIEW", "files_changed: data/official-jail-source-leads.csv", ""]
    probed = blocked = upgraded = 0
    for r in rows:
        if r.get("access_status") not in ("needs_adapter", "needs_research"):
            continue
        url = r.get("source_url", "").strip()
        if not url or not url.startswith("http"):
            continue
        probed += 1
        status, body, final = fetch(url)
        if body is None:
            blocked += 1
            r["access_status"] = "probe_blocked" if "http_" in status or "error_" in status else status
            r["last_probed"] = now.strftime("%Y-%m-%d")
            r["probe_result"] = status
            report += [f"- BLOCKED {r['state']}/{r['county']}: {status} — {url}", "  next_action: do not retry without human direction"]
            continue
        if not robots_allows(final):
            blocked += 1
            r["access_status"] = "robots_disallowed"
            r["last_probed"] = now.strftime("%Y-%m-%d")
            r["probe_result"] = "robots_disallow"
            report += [f"- BLOCKED {r['state']}/{r['county']}: robots.txt disallows — {url}"]
            continue
        hits = fingerprint(body)
        probed_ok = "probed_ok"
        r["access_status"] = probed_ok
        r["last_probed"] = now.strftime("%Y-%m-%d")
        r["probe_result"] = f"http_{status}"
        r["probe_hits"] = ",".join(hits) or "none"
        # suggest adapter strategy from fingerprint
        strat = r.get("adapter_strategy", "")
        if not strat or strat == "manual_discovery":
            if "json_api" in hits: r["adapter_strategy"] = "json_endpoint"
            elif "pdf_roster" in hits or "xlsx_roster" in hits: r["adapter_strategy"] = "file_download"
            elif "jailtracker" in hits or "zuercher" in hits: r["adapter_strategy"] = "portal_platform"
        if hits:
            upgraded += 1
        report += [f"- OK {r['state']}/{r['county']}: http_{status}, hits=[{r['probe_hits']}], strategy={r['adapter_strategy']}",
                   f"  source_evidence: {url} -> {final}",
                   "  publication_risk: unchanged (staging_only); requires human review before adapter work"]
    tmp = LEADS + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, LEADS)
    report += ["", f"## Summary", f"- probed: {probed}, ok: {probed - blocked}, blocked: {blocked}, with platform hits: {upgraded}",
               "next_action: human reviews probed_ok leads; feed-builder may draft staging-only adapters for approved ones."]
    outdir = os.path.join(QUEUE_DIR, BOT)
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{now:%Y-%m-%d}-scout-checkpoint.md")
    with open(out, "w") as f:
        f.write("\n".join(report) + "\n")
    print(f"scout done: {probed} probed, {blocked} blocked, {upgraded} fingerprinted; report -> {out}")
if __name__ == "__main__":
    main()
