#!/usr/bin/env python3
"""Test all html_roster leads — classify which work, which are JS-rendered, etc."""
import csv
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import httpx
import psycopg
from psycopg.rows import dict_row


def find_api_in_js(html: str) -> list:
    """Look for API endpoints embedded in JS code."""
    apis = set()
    # Common patterns
    patterns = [
        r'["\'](https?://[^"\']+/(?:api|roster|inmates|bookings|jail)[^"\']*)["\']',
        r'["\'](/[^"\']*(?:api|roster|inmates|bookings|jail)[^"\']*)["\']',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[a-z]+\(["\']([^"\']+)["\']',
        r'url:\s*["\']([^"\']+)["\']',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html, re.IGNORECASE):
            apis.add(m.group(1))
    return sorted(apis)


def find_json_ld(html: str) -> list:
    """Look for JSON-LD or embedded JSON data."""
    blobs = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL):
        blobs.append(m.group(1).strip()[:200])
    for m in re.finditer(r'window\.__data\s*=\s*(\{.*?\});', html, re.DOTALL):
        blobs.append(m.group(1)[:200])
    for m in re.finditer(r'window\.INITIAL_STATE\s*=\s*(\{.*?\});', html, re.DOTALL):
        blobs.append(m.group(1)[:200])
    return blobs


def main():
    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
    leads = conn.execute('''
        SELECT q.source_url, q.adapter, c.name as county_name, s.abbrev as state
        FROM records.county_ingestion_queue q
        JOIN public."County" c ON c.id = q.county_id
        JOIN public."State" s ON s.id = c."stateId"
        WHERE q.adapter = 'html_roster_staging'
        AND q.status = 'adapter_needed'
        ORDER BY s.abbrev, c.name
    ''').fetchall()
    conn.close()

    print(f"Testing {len(leads)} html_roster leads...")

    out_path = Path("/src/data/national/adapter-test-results.csv")
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["state", "county", "url", "status", "record_count", "table_count", "api_urls_found", "notes"])

        with httpx.Client(timeout=15, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        }) as client:
            for r in leads:
                state = r["state"]
                county = r["county_name"]
                url = r["source_url"]

                try:
                    resp = client.get(url)
                    html = resp.text or ""

                    tables = len(re.findall(r"<table", html, re.IGNORECASE))
                    th_cells = re.findall(r"<th[^>]*>(.*?)</th>", html, re.DOTALL | re.IGNORECASE)
                    api_urls = find_api_in_js(html)
                    json_ld = find_json_ld(html)

                    # Try html_roster parse
                    from backend.adapters.html_roster import fetch
                    source = {"state": state, "county": county, "facility_name": f"{county} County Jail", "source_url": url}
                    try:
                        records = fetch(source)
                        if records:
                            writer.writerow([state, county, url, "works", len(records), tables, "", f"Parsed {len(records)} records from {tables} tables"])
                            continue
                    except Exception as e:
                        parse_err = str(e)[:100]
                        # fall through to classification

                    # Classify the page
                    if tables == 0:
                        if api_urls:
                            writer.writerow([state, county, url, "api_found", 0, 0, "|".join(api_urls[:5]), f"JS-rendered, {len(api_urls)} API URLs found"])
                        elif json_ld:
                            writer.writerow([state, county, url, "js_rendered", 0, 0, "", f"JS-rendered with {len(json_ld)} JSON blobs"])
                        else:
                            writer.writerow([state, county, url, "needs_playwright", 0, 0, "", f"No tables, APIs, or JSON found — likely JS-rendered"])
                    elif th_cells:
                        # Has table headers — try to parse
                        identity_headers = [h for h in th_cells if any(k in h.lower() for k in ["name", "booking", "inmate", "last", "first"])]
                        if identity_headers:
                            writer.writerow([state, county, url, "works_maybe", 0, tables, "", f"Has identity columns: {[h[:30] for h in identity_headers[:3]]}"])
                        else:
                            writer.writerow([state, county, url, "no_identity_col", 0, tables, "", f"Tables found but no identity columns"])
                    else:
                        writer.writerow([state, county, url, "empty", 0, tables, "", f"Page returned 0 records from {tables} tables"])

                except httpx.TimeoutException:
                    writer.writerow([state, county, url, "dead", 0, 0, "", "Connection timed out"])
                except httpx.ConnectError:
                    writer.writerow([state, county, url, "dead", 0, 0, "", "Connection refused/dns error"])
                except Exception as e:
                    writer.writerow([state, county, url, "error", 0, 0, "", str(e)[:100]])

    # Print summary
    with out_path.open() as f:
        reader = csv.DictReader(f)
        from collections import Counter
        counts = Counter(row["status"] for row in reader)
    print("\n=== Results Summary ===")
    for status, count in counts.most_common():
        print(f"  {status:20s} {count}")
    print(f"\nFull results: {out_path}")


if __name__ == "__main__":
    main()
