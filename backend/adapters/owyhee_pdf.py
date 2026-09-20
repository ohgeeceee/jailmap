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


def _find_working_pdf(url: str) -> Optional[str]:
    """Find a working PDF link by trying different suffix patterns."""
    import httpx
    
    # First try the URL as-is
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            return url
    except Exception:
        pass
    
    # Try to find the PDF by incrementing the suffix number
    # Pattern: JailRoster-N.pdf or JailRoster.pdf
    base = re.sub(r'-\d+\.pdf$', '', url)
    if base != url:
        for i in range(1, 30):
            try:
                r = httpx.get(f"{base}-{i}.pdf", timeout=10, follow_redirects=True)
                if r.status_code == 200:
                    return f"{base}-{i}.pdf"
            except Exception:
                continue
    
    return None


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
    # The jail page has buttons linking to PDFs
    jail_url = source.get("source_url", "").rstrip("/")
    if "/wp-content/uploads" in jail_url:
        jail_url = jail_url.split("/wp-content/uploads")[0] + "/jail/"
    text = _fetch_html(jail_url).decode("utf-8", errors="ignore")
    pulled_at = datetime.now(timezone.utc).isoformat()
    records: List[Dict] = []

    pdf_links = re.findall(r"https?://[^\"'<> ]+JailRoster[^\"'<> ]*\.pdf", text)
    if not pdf_links:
        return AdapterResult(source, [])

    # Find a PDF link that actually works (200 response)
    pdf_url = _find_working_pdf(pdf_links[0])
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

    # Parse the Owyhee County PDF format:
    # Each line is: LASTNAME FIRSTNAME MIDDLE BOOKING# NEXT_RELEASE FINAL_RELEASE
    # Example: ALVAREZ JUAREZ, SHEIK DOMINIQUE 26BK117 **:**:** **/**/**
    
    for line in pdf_text.splitlines():
        line = _clean_text(line)
        if not line:
            continue
        
        # Skip header lines
        if line.startswith("Report Includes:") or line.startswith("Inmate Name"):
            continue
        
        # Match pattern: NAME BOOKING# TIME DATE DATE
        # Booking# format: 26BK117 (year + letters + number)
        match = re.match(
            r'^(?P<name>[^0-9]+?)\s+(?P<booking>\d{2}[A-Z]{2}\d+)\s+'
            r'(?P<next_release>[\*\d:]+\s+[\*\d/]+)\s+'
            r'(?P<final_release>[\*\d/]+)$',
            line
        )
        
        if match:
            name = match.group("name").strip()
            booking_number = match.group("booking").strip()
            
            # Parse name: "LASTNAME, FIRSTNAME MIDDLE" or "FIRSTNAME LASTNAME"
            if "," in name:
                parts = name.split(",", 1)
                last_name = parts[0].strip()
                first_name = parts[1].strip()
            else:
                parts = name.split()
                first_name = parts[0] if parts else ""
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            
            records.append({
                "state": "ID",
                "county": source["county"],
                "facility": source["facility_name"],
                "source_url": pdf_url,
                "source_type": "pdf",
                "source_updated_at": pulled_at,
                "booking_number": booking_number,
                "full_name": f"{first_name} {last_name}".strip(),
                "first_name": first_name,
                "last_name": last_name,
                "dob": None,
                "age": None,
                "sex": None,
                "race": None,
                "booking_date": None,
                "release_date": None,
                "charges": [],
                "bond_amount": None,
                "status": "in_custody", "visibility": "public",
                "mugshot_url": None,
                "notes": None,
            })

    return AdapterResult(source, records)
