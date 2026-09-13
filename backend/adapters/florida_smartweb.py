"""SmartWEB adapter using browser automation for rendered HTML."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


class AdapterResult:
    def __init__(self, source, records):
        self.source = source
        self.records = records


def fetch_html(url: str) -> str:
    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        return client.get(url, headers=HEADERS).text


def smartweb_via_browser(url: str, county: str, facility: str) -> AdapterResult:
    """Use browser automation to get rendered HTML from SmartWEB portal."""
    from hermes_tools import browser_exec
    
    code = f"""
from hermes_tools import browser_exec
result = browser_exec(
    code=\'\'\'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
driver.get('{url}')

# Wait for page to load
time.sleep(5)

# Click search if needed
try:
    search_btn = driver.find_element(By.NAME, 'btnSumit')
    search_btn.click()
    time.sleep(3)
except:
    pass

html = driver.page_source
driver.quit()

print(html)
\'\'\',
    timeout=30
)
print(result.get('output', ''))
"""
    
    try:
        result = browser_exec(code=code, timeout=30)
        html = result.get('output', '')
        records = smartweb_parse_page(html, url, county, facility)
        return AdapterResult({'url': url, 'county': county, 'facility_name': facility}, records)
    except Exception as e:
        return AdapterResult({'url': url, 'county': county, 'facility_name': facility}, [])


def smartweb_parse_page(html: str, source_url: str, county: str = "", facility: str = "") -> List[Dict]:
    """Parse SmartWEB rendered HTML page."""
    records = []
    now = datetime.now(timezone.utc).isoformat()
    
    if not html:
        return []
    
    # Find GridView table
    grid_match = re.search(r'<table[^>]*id="gvInmates"[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if not grid_match:
        grid_match = re.search(r'<table[^>]*id="MainContent_gvInmates"[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    
    if not grid_match:
        return []
    
    table = grid_match.group(1)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
    
    current_record = {}
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
        cell_texts = [re.sub(r"<[^>]+>", " ", c).strip() for c in cells]
        cell_texts = [re.sub(r"\s+", " ", t).strip() for t in cell_texts]
        
        if not cell_texts:
            continue
        
        first_cell = cell_texts[0] if cell_texts else ""
        
        # New inmate starts with "Enlarge Photo"
        if "Enlarge Photo" in first_cell or (len(cell_texts) >= 2 and "Enlarge Photo" in cell_texts[0]):
            # Save previous record
            if current_record.get("full_name"):
                records.append(current_record)
            
            # Extract name from second cell
            if len(cell_texts) > 1:
                name_text = cell_texts[1]
                m = re.match(r"([A-Z][A-Z\s,]+)\s*\(\s*([A-Z]+)\s*/\s*([A-Z/]+)\s*/\s*DOB:\s*(\d{1,2}/\d{1,2}/\d{4})\)", name_text)
                if m:
                    full_name = m.group(1).strip()
                    sex = m.group(2).strip()
                    race = m.group(3).strip()
                    dob = m.group(4).strip()
                    
                    if "," in full_name:
                        parts = full_name.split(",", 1)
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                    else:
                        first_name = ""
                        last_name = full_name
                    
                    current_record = {
                        "full_name": full_name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "sex": sex,
                        "race": race,
                        "dob": dob,
                    }
                else:
                    current_record = {"full_name": name_text}
            continue
        
        # Label: value pairs
        for i, cell in enumerate(cell_texts):
            if cell.endswith(":") and i + 1 < len(cell_texts):
                label = cell[:-1].lower()
                value = cell_texts[i + 1]
                if "booking no" in label:
                    current_record["booking_number"] = value
                elif "booking date" in label:
                    current_record["booking_date"] = value
                elif "status" in label:
                    current_record["status"] = value
                elif "age" in label and "booking" in label:
                    current_record["age"] = value
    
    if current_record.get("full_name"):
        records.append(current_record)
    
    # Format
    formatted = []
    for rec in records:
        formatted.append({
            "state": "FL",
            "county": rec.get("county", county),
            "facility": rec.get("facility", facility),
            "source_url": source_url,
            "source_type": "smartweb",
            "pulled_at": now,
            "booking_number": rec.get("booking_number", ""),
            "full_name": rec.get("full_name", ""),
            "first_name": rec.get("first_name", ""),
            "last_name": rec.get("last_name", ""),
            "booking_date": rec.get("booking_date", ""),
            "charges": [{"source_id": "c1", "description": "Unknown", "statute": None, "severity": None}],
            "age": rec.get("age"),
            "sex": rec.get("sex"),
            "race": rec.get("race"),
            "status": rec.get("status", "in_custody").lower().replace(" ", "_"),
        })
    
    return formatted


def smartweb_county(source: Dict[str, Any]) -> AdapterResult:
    """SmartWEB adapter for any county using the portal."""
    url = source.get("source_url")
    county = source.get("county", "")
    facility = source.get("facility_name", f"{county} County Jail")
    
    return smartweb_via_browser(url, county, facility)
