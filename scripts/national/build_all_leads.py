#!/usr/bin/env python3
"""Final end-to-end pipeline for building JailMap source leads."""
import csv
import re
from pathlib import Path

FIELDS = [
    "state", "county", "facility", "source_url", "source_owner",
    "source_kind", "access_status", "adapter_strategy",
    "publication_default", "evidence_url", "notes",
]

URL_RE = re.compile(r'^https?://\S+', re.IGNORECASE)
HTTPS_RE = re.compile(r'^https://\S+', re.IGNORECASE)

ACCESS_MAP = {
    "html_roster": "needs_adapter",
    "pdf_roster": "needs_adapter",
    "search_form": "needs_adapter",
    "vendor_portal": "needs_adapter",
    "smartweb_portal": "needs_adapter",
    "socrata_open_data_portal": "needs_adapter",
    "zuercher_portal": "needs_adapter",
    "citizenrims_portal": "needs_adapter",
    "tyler_jailtracker_portal": "needs_adapter",
    "tyler_odyssey_portal": "needs_adapter",
    "no_roster_found": "no_public_source",
    "blocked": "blocked",
    "login_required": "blocked",
    "captcha_gated": "blocked",
    "staging_only": "needs_adapter",
    "manual_discovery": "needs_research",
}

SOURCE_KIND_MAP = {
    "html_roster": "html_roster",
    "pdf_roster": "pdf_roster",
    "search_form": "search_form",
    "vendor_portal": "vendor_portal",
    "smartweb_portal": "vendor_portal",
    "socrata_open_data_portal": "vendor_portal",
    "zuercher_portal": "vendor_portal",
    "citizenrims_portal": "vendor_portal",
    "tyler_jailtracker_portal": "vendor_portal",
    "tyler_odyssey_portal": "vendor_portal",
}

STRATEGY_MAP = {
    "html_roster": "html_roster_staging",
    "pdf_roster": "pdf_roster_staging",
    "smartweb_portal": "smartweb_staging",
    "socrata_open_data_portal": "socrata_staging",
    "zuercher_portal": "zuercher_staging",
    "citizenrims_portal": "citizenrims_staging",
    "tyler_jailtracker_portal": "tyler_staging",
    "tyler_odyssey_portal": "tyler_staging",
    "search_form": "search_form",
}

VALID_SOURCES = {
    "html_roster", "pdf_roster", "search_form", "vendor_portal",
    "smartweb_portal", "socrata_open_data_portal", "zuercher_portal",
    "citizenrims_portal", "tyler_jailtracker_portal", "tyler_odyssey_portal",
}

ALLOWED_ACCESS = {"needs_research", "needs_adapter", "blocked", "active_staging", "no_public_source"}
ALLOWED_PUB = {"staging_only", "blocked", "aggregate_only"}

STATE_ABBRS = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}

COUNTY_STATE_MAP = {}

def build_county_map():
    with open("data/national/source-census.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip().lower()
            county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
            if len(state) == 2 and county_clean:
                COUNTY_STATE_MAP[county_clean] = state
    with open("data/national/census-follow.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip().lower()
            county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county).strip()
            if len(state) == 2 and county_clean:
                COUNTY_STATE_MAP[county_clean] = state
    COUNTY_STATE_MAP.update({
        "calhoun": "AL", "franklin": "AL", "escambia": "AL", "jackson": "AL",
        "houston": "AL", "lauderdale": "AL", "limestone": "AL", "mobile": "AL",
        "montgomery": "AL", "st mary": "LA", "outagamie": "WI",
        "greenbrier": "WV", "mineral": "WV",
    })

def extract_state_from_url(url):
    if not url:
        return ""
    url_lower = url.lower()
    patterns = [
        r'county([a-z]{2})(?:\.gov|\.us|\.org|\.com|/)',
        r'county-([a-z]{2})(?:\.gov|\.us|\.org|\.com|/)',
        r'county_([a-z]{2})(?:\.gov|\.us|\.org|\.com|/)',
        r'\.([a-z]{2})(?:\.gov|\.us|\.org)',
        r'\.([a-z]{2})(?:\.gov|\.us|\.org|\.com)/',
    ]
    for pattern in patterns:
        m = re.search(pattern, url_lower)
        if m and m.group(1).upper() in STATE_ABBRS:
            return m.group(1).upper()
    return ""

def infer_state(county, url):
    county_lower = county.lower()
    county_clean = re.sub(r'\s+(county|parish|borough|census area).*', '', county_lower).strip()
    state = extract_state_from_url(url)
    if state:
        return state
    if county_clean in COUNTY_STATE_MAP:
        return COUNTY_STATE_MAP[county_clean]
    return ""

def fix_state(row):
    state = (row.get("state") or "").strip()
    if len(state) == 2 and state.isalpha() and state.isupper():
        return state
    county = (row.get("county") or "").strip()
    url = (row.get("source_url") or "").strip()
    inferred = infer_state(county, url)
    return inferred.upper() if inferred else ""

def normalize_url(raw):
    s = (raw or "").strip()
    if not s:
        return ""
    if HTTPS_RE.match(s):
        return s
    if URL_RE.match(s):
        return "https://" + s[7:]
    if "." in s and " " not in s:
        return "https://" + s
    return ""

def classify(row):
    vendor = (row.get("vendor_family") or "").strip()
    access = (row.get("access_class") or "").strip()
    if vendor in VALID_SOURCES:
        if access in ("staging_only", "no_roster_found", "blocked", "login_required", "captcha_gated"):
            return vendor, access
        return vendor, "staging_only"
    if access in VALID_SOURCES:
        return access, "staging_only"
    return "", ""

def process_source_file(path):
    rows = []
    seen = set()
    stats = {"processed": 0, "no_source": 0, "no_url": 0, "written": 0}

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["processed"] += 1
            vendor, pub_default = classify(row)
            if not vendor:
                stats["no_source"] += 1
                continue

            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip()
            facility = (row.get("jail") or "").strip()
            if not facility:
                facility = f"{county} — auto-discovered"
            candidate_url = (row.get("candidate_url") or "").strip()
            final_url = (row.get("final_url") or "").strip()
            evidence = (row.get("evidence") or "").strip()
            notes = (row.get("notes") or "").strip()
            access = pub_default

            source_url = ""
            for u in (final_url, candidate_url):
                source_url = normalize_url(u)
                if source_url:
                    break
            if not source_url:
                stats["no_url"] += 1
                continue

            if not notes:
                notes = f"{vendor} access={access} — {source_url}"

            evidence_url = normalize_url(evidence)
            if not evidence_url:
                evidence_url = source_url

            source_kind = SOURCE_KIND_MAP.get(vendor, "html_roster")
            adapter_strategy = STRATEGY_MAP.get(vendor, "html_roster_staging")
            access_status = ACCESS_MAP.get(vendor, "needs_adapter")

            if pub_default in ("no_roster_found", "blocked", "login_required", "captcha_gated"):
                pub = "blocked"
            else:
                pub = "staging_only"

            key = (state, county.lower(), source_url)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "state": state,
                "county": county,
                "facility": facility,
                "source_url": source_url,
                "source_owner": vendor or "county_sheriff",
                "source_kind": source_kind,
                "access_status": access_status,
                "adapter_strategy": adapter_strategy,
                "publication_default": pub,
                "evidence_url": evidence_url,
                "notes": notes,
            })
            stats["written"] += 1

    return rows, stats

def process_existing_leads(path):
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = (row.get("state") or "").strip().upper()
            county = (row.get("county") or "").strip()
            source_url = normalize_url(row.get("source_url", ""))
            evidence_url = normalize_url(row.get("evidence_url", ""))
            if not evidence_url:
                evidence_url = source_url
            source_owner = (row.get("source_owner") or "").strip() or "county_sheriff"
            source_kind = (row.get("source_kind") or "").strip() or "html_roster"
            access_status = (row.get("access_status") or "").strip()
            adapter_strategy = (row.get("adapter_strategy") or "").strip() or "html_roster_staging"
            pub_default = (row.get("publication_default") or "").strip() or "staging_only"
            if access_status not in ALLOWED_ACCESS:
                access_status = "needs_adapter"
            if pub_default not in ALLOWED_PUB:
                pub_default = "staging_only"

            if not source_url:
                continue

            notes = (row.get("notes") or "").strip()
            if not notes:
                notes = f"Existing lead: {source_owner}/{source_kind} — {source_url}"
            facility = (row.get("facility") or "").strip()
            if not facility:
                facility = f"{county} — auto-discovered"

            rows.append({
                "state": state,
                "county": county,
                "facility": facility,
                "source_url": source_url,
                "source_owner": source_owner,
                "source_kind": source_kind,
                "access_status": access_status,
                "adapter_strategy": adapter_strategy,
                "publication_default": pub_default,
                "evidence_url": evidence_url,
                "notes": notes,
            })
    return rows

def main():
    build_county_map()

    all_rows = []

    # 1. Existing leads file (fix bad state codes)
    existing_all = process_existing_leads(Path("data/national/official-jail-source-leads.csv"))
    existing = []
    dropped = 0
    for r in existing_all:
        fixed = fix_state(r)
        if not fixed:
            dropped += 1
            continue
        r["state"] = fixed
        existing.append(r)
    all_rows.extend(existing)
    print(f"Existing leads: {len(existing)} (dropped {dropped} with unfixable state)")

    # 2. source-census.csv
    census_rows, stats = process_source_file(Path("data/national/source-census.csv"))
    all_rows.extend(census_rows)
    print(f"source-census.csv: {stats['written']} leads (from {stats['processed']} rows)")

    # 3. census-follow-final.csv (recovered)
    follow_rows, stats = process_source_file(Path("data/national/census-follow-final.csv"))
    all_rows.extend(follow_rows)
    print(f"census-follow-final.csv: {stats['written']} leads (from {stats['processed']} rows)")

    # Deduplicate by (state, county, source_url)
    seen = set()
    unique = []
    for r in all_rows:
        key = (r["state"], r["county"].lower(), r["source_url"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    print(f"\nTotal unique leads: {len(unique)}")

    # Write final
    out_path = Path("data/national/leads-final.csv")
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(unique)

    print(f"Written to: {out_path}")

if __name__ == "__main__":
    main()
