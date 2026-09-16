#!/usr/bin/env python3
"""Verify Carter dmxConnect API + CivicPlus APIClient endpoints. Read-only."""
import httpx, json
H = {"User-Agent": "Mozilla/5.0 (compatible; JailMap/1.0; +https://jailmap.com)"}
def peek(name, url):
    print(f"== {name}: {url}")
    try:
        with httpx.Client(timeout=20, follow_redirects=True, headers=H) as c:
            r = c.get(url)
            ct = r.headers.get("content-type", "")
            print(f"   status {r.status_code} ctype {ct} bytes {len(r.content)}")
            if "json" in ct:
                try:
                    d = r.json()
                    print(f"   json keys: {list(d)[:10] if isinstance(d, dict) else type(d)}")
                    print("   sample:", json.dumps(d, default=str)[:500])
                except Exception as e:
                    print(f"   json parse fail: {e}; head: {r.text[:300]!r}")
            else:
                print("   head:", r.text[:300].replace(chr(10), " ")[:300])
    except Exception as e:
        print(f"   error {type(e).__name__}: {e}")
    print()
peek("Carter Read", "https://cartercountysheriff.us/dmxConnect/api/Booking/Read.php")
peek("Carter Read2", "https://cartercountysheriff.us/dmxConnect/api/Booking/Read2.php")
peek("Carter Alerts", "https://cartercountysheriff.us/dmxConnect/api/Alerts/currentAlert.php")
peek("Cascade APIClient", "https://www.cascadecountymt.gov/Assets/Scripts/APIClient.js")
peek("SilverBow APIClient", "https://co.silverbow.mt.us/Assets/Scripts/APIClient.js")
peek("Cascade PDF", "https://ccmtgov-my.sharepoint.com/:b:/g/personal/jailroster_cascadecountymt_gov/EbIMNOlpS-pNj2V6jtlc11YBzi2NN7EmcmLK4hRFY4pTGw?e=NvKMHS")
peek("LC PDF", "https://www.lccountymt.gov/files/assets/county/v/225/sheriff/documents/jail_roster.pdf")
