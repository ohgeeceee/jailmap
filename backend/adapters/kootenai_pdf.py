from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_common_text_record, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _extract_pdf_text(pdf_url: str) -> str:
    """Extract text from a PDF URL using pypdfium2."""
    import httpx
    import pypdfium2 as pdfium
    
    resp = httpx.get(pdf_url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    
    pdf_text = ""
    try:
        pdf = pdfium.PdfDocument(resp.content)
        for page in pdf:
            textpage = page.get_textpage()
            pdf_text += textpage.get_text_bounded() + "\n"
    except Exception:
        pass
    
    return pdf_text


def parse(source, pdf_reader=None, pdf_text_provider=None) -> AdapterResult:
    """Parse Kootenai County PDF inmate roster."""
    pdf_url = source.get("source_url", "").rstrip("/")
    if not pdf_url.endswith(".pdf"):
        # Find the PDF link on the sheriff page
        text = _fetch_html(pdf_url).decode("utf-8", errors="ignore")
        pdfs = re.findall(r'href="([^"]*\.pdf)"', text, re.IGNORECASE)
        # Look for the current inmate list PDF
        pdf_url = None
        for p in pdfs:
            if "currentinmatelist" in p.lower():
                pdf_url = p
                break
        if not pdf_url:
            return AdapterResult(source, [])
    
    pdf_text = ""
    if pdf_text_provider:
        pdf_text = pdf_text_provider(pdf_url) or ""
    else:
        try:
            pdf_text = _extract_pdf_text(pdf_url)
        except Exception:
            pdf_text = ""
    
    if not pdf_text:
        return AdapterResult(source, [])
    
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []
    
    # Parse Kootenai County PDF format
    # Format: "LASTNAME, FIRST MIDDLE" (uppercase)
    # Followed by structured fields
    lines = pdf_text.splitlines()
    i = 0
    while i < len(lines):
        line = _clean_text(lines[i])
        
        # Skip header lines
        if not line or "Current Inmate List" in line or "Page " in line:
            i += 1
            continue
        
        # Skip the "Current as of" line
        if line.startswith("Current as of"):
            i += 1
            continue
        
        # Check if this looks like a name line
        # Format: "LASTNAME, FIRST MIDDLE" (uppercase, comma-separated)
        name_match = re.match(r'^([A-Z][A-Z\s\-\']+),\s+([A-Z][A-Z\s\-\']+)$', line)
        
        if name_match:
            last_name = name_match.group(1).strip()
            first_name = name_match.group(2).strip()
            full_name = f"{first_name} {last_name}"
            
            # Parse the next lines for this record
            booking_date = None
            release_date = None
            charges = []
            bond_amount = None
            
            # Look ahead for fields
            j = i + 1
            while j < len(lines):
                next_line = _clean_text(lines[j])
                
                # Stop if we hit another name or header
                if re.match(r'^([A-Z][A-Z\s\-\']+),\s+([A-Z][A-Z\s\-\']+)$', next_line):
                    break
                if "Current Inmate List" in next_line:
                    break
                if next_line.startswith("Current as of"):
                    break
                
                # Parse incarceration date
                inc_match = re.search(r'Incarceration Date:\s+(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M)', next_line)
                if inc_match:
                    booking_date = inc_match.group(1)
                
                # Parse scheduled release
                rel_match = re.search(r'Scheduled Release Date:\s*(\d{1,2}/\d{1,2}/\d{4})', next_line)
                if rel_match:
                    release_date = rel_match.group(1)
                
                # Parse charge lines (format: "DATE TIME DESCRIPTION CASE# BOND")
                # Example: "7/28/2026 12:30:00PM US Marshal Hold 2607USM $0.00"
                charge_match = re.match(
                    r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M)\s+'
                    r'(.+?)\s+'
                    r'(\d{4}[A-Z]{2,4})\s+'
                    r'\$?([\d,]+\.?\d*)$',
                    next_line
                )
                if charge_match:
                    charge_desc = charge_match.group(2).strip()
                    case_num = charge_match.group(3)
                    bond = charge_match.group(4)
                    charges.append({
                        "source_id": case_num,
                        "description": charge_desc,
                        "statute": None,
                        "severity": None,
                    })
                    if bond_amount is None and bond != "0.00":
                        try:
                            bond_amount = float(bond.replace(",", ""))
                        except ValueError:
                            pass
                
                j += 1
            
            records.append({
                "state": "ID",
                "county": source["county"],
                "facility": source["facility_name"],
                "source_url": pdf_url,
                "source_type": "pdf",
                "pulled_at": pulled_at,
                "booking_number": None,
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "dob": None,
                "age": None,
                "sex": None,
                "race": None,
                "booking_date": booking_date,
                "release_date": release_date,
                "charges": charges or [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}],
                "bond_amount": bond_amount,
                "status": "in_custody",
                "mugshot_url": None,
                "notes": None,
            })
        
        i += 1
    
    return AdapterResult(source, records)
