#!/usr/bin/env python3
"""Probe standard_json counties' landing pages for their real roster endpoints.
Read-only. Prints candidate URLs found in each page."""
import os, re, psycopg, httpx
URLS = {
 "Cascade": "https://www.cascadecountymt.gov/314/Inmate-Roster",
 "Chouteau": "https://chouteaucountysheriff.com/",
 "Custer": "https://custercountymt.gov/emergency-enforcement/sheriff/",
 "Carter": "https://cartercountysheriff.us/inmate-search",
 "Fergus": "https://fergusmt.gov/detention-center-roster",
 "Lewis and Clark": "https://www.lccountymt.gov/Sheriff/Detention-Center",
 "Silver Bow": "https://co.silverbow.mt.us/3274/Detention-Center",
}
PAT = re.compile(r"(?:href|src|url|data-url)\s*[=:]\s*[\"']([^\"']*(?:json|roster|inmate|api|feeds?)[^\"']*)[\"']", re.I)
with httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)"}) as c:
    for county, url in URLS.items():
        print(f"== {county}: {url}")
        try:
            r = c.get(url)
            print(f"   status {r.status_code}, {len(r.text)} bytes")
            hits = sorted({m for m in PAT.findall(r.text)})[:12]
            for h in hits:
                print(f"   candidate: {h}")
            if not hits:
                # look for anything embedded in scripts that looks like data
                js = re.findall(r"[\"'](/[A-Za-z0-9_./-]*(?:Json|JSON|Inmates| inmates)[A-Za-z0-9_./?=-]*)[\"']", r.text)
                for j in sorted(set(js))[:8]:
                    print(f"   js-path: {j}")
        except Exception as e:
            print(f"   error: {type(e).__name__}: {e}")
        print()
