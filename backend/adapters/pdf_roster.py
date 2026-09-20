from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.adapters.idaho import AdapterResult, _fetch_html, _parse_iso


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _extract_pdf_text(pdf_url: str) -> str:
    """Extract text from a PDF URL using pypdfium2."""
    import httpx
    import pypdfium2 as pdfium

    resp = httpx.get(pdf_url, timeout=30, follow_redirects=True, verify=False)
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


def _find_pdf_url(page_url: str) -> Optional[str]:
    """Find a PDF link on a roster page."""
    try:
        text = _fetch_html(page_url).decode("utf-8", errors="ignore")
    except Exception:
        return None

    # Look for PDF links
    pdfs = re.findall(r'href="([^"]*\.pdf[^"]*)"', text, re.IGNORECASE)
    for p in pdfs:
        if "inmate" in p.lower() or "roster" in p.lower() or "jail" in p.lower():
            if p.startswith("http"):
                return p
            elif p.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(page_url)
                return f"{parsed.scheme}://{parsed.hostname}{p}"
    return None


def parse(source, pdf_reader=None, pdf_text_provider=None) -> AdapterResult:
    """Generic PDF roster parser. Tries to extract name, booking date, charges from text."""
    source_url = source.get("source_url", "").rstrip("/")
    pulled_at = datetime.now(timezone.utc).isoformat()

    # Find PDF URL
    pdf_url = None
    if source_url.endswith(".pdf"):
        pdf_url = source_url
    else:
        pdf_url = _find_pdf_url(source_url)

    if not pdf_url:
        return AdapterResult(source, [])

    # Extract PDF text
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

    records: List[Dict] = []

    # Generic name pattern: "Last, First Middle" or "First Last"
    # Try to find booking records in the PDF text
    lines = pdf_text.splitlines()

    for line in lines:
        line = _clean_text(line)
        if not line or len(line) < 5:
            continue

        # Match "Last, First" pattern
        name_match = re.match(r'^([A-Z][a-zA-Z\s\-\']+?),\s+([A-Z][a-zA-Z\s\-\']+)$', line)
        if name_match:
            last_name = name_match.group(1).strip()
            first_name = name_match.group(2).strip()

            # Validate: last name should be short, first name too
            if len(last_name) > 30 or len(first_name) > 30:
                continue
            if " " in last_name and "," in last_name:
                continue

            records.append({
                "state": source.get("state", ""),
                "county": source["county"],
                "facility": source.get("facility_name", ""),
                "source_url": source_url,
                "source_type": "pdf",
                "source_updated_at": pulled_at,
                "booking_number": None,
                "full_name": f"{first_name} {last_name}",
                "first_name": first_name,
                "last_name": last_name,
                "dob": None,
                "age": None,
                "sex": None,
                "race": None,
                "booking_date": pulled_at.split(".")[0] + "Z",
                "release_date": None,
                "charges": [{"source_id": "c1", "description": "Charge details in PDF", "statute": None, "severity": None}],
                "bond_amount": None,
                "status": "in_custody", "visibility": "public",
                "mugshot_url": None,
                "notes": None,
            })

    return AdapterResult(source, records)
