from datetime import datetime, timezone
from typing import Dict, List, Optional
import os
import httpx
from urllib.parse import urlparse

REQUIRED_HEADERS = {
    "User-Agent": "jailmap/1.0 (+https://jailmap.com; contact ops@jailmap.com)",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
def _load_allowed_hosts():
    """Load allowed hosts from file or env var."""
    hosts = set()
    # Try file first (allows long lists)
    for path in ['/app/data/allowed_hosts.txt', 'data/allowed_hosts.txt']:
        try:
            with open(path) as f:
                hosts.update(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            pass
    # Fall back to env var
    env_hosts = os.environ.get("SOURCE_ALLOWED_HOSTS", "")
    if env_hosts:
        hosts.update(h.strip() for h in env_hosts.split(",") if h.strip())
    return hosts

ALLOWED_HOSTS = _load_allowed_hosts()


class AdapterResult:
    def __init__(self, source, records):
        self.source = source
        self.records = records


def _assert_authorized(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("Source endpoint is not authorized")
    hostname = parsed.hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if ALLOWED_HOSTS and hostname not in ALLOWED_HOSTS:
        raise ValueError("Source endpoint host is not allowed")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_status(status: Optional[str]) -> str:
    if not status:
        return "in_custody"
    value = str(status).strip().lower()
    if value in {"in_custody", "inmate", "incarcerated", "in"}:
        return "in_custody"
    if value in {"released", "out", "discharged"}:
        return "released"
    if value in {"transferred", "transfer", "moved"}:
        return "transferred"
    return "in_custody"


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return None


def _extract_text(node: Dict) -> str:
    if not isinstance(node, dict):
        return ""
    text = node.get("text") or node.get("content") or node.get("value") or ""
    return str(text).strip()


def _node_texts(*nodes: Optional[Dict]) -> List[str]:
    texts = []
    for node in nodes:
        if node and isinstance(node, dict):
            texts.append(_extract_text(node))
            children = node.get("children")
            if isinstance(children, list):
                texts.extend(_extract_text(child) for child in children if isinstance(child, dict))
    return [t for t in texts if t]


def _parse_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            continue
    return value


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _join_charges(*parts: Optional[str]) -> str:
    joined = " | ".join(p.strip() for p in parts if p and str(p).strip())
    return joined or "Unknown charge"


def _charges_from_text(text: str) -> List[Dict]:
    if not text:
        return [{"source_id": "c1", "description": "Unknown charge", "statute": None, "severity": None}]
    return [{"source_id": "c1", "description": text, "statute": None, "severity": None}]


def _parse_common_text_record(fields: Dict[str, Optional[str]], source_url: str) -> Dict:
    full_name = _first_non_empty(fields.get("name"), fields.get("inmate_name"), fields.get("full_name")) or ""
    first_name = fields.get("first_name") or ""
    last_name = fields.get("last_name") or ""
    if not first_name and not last_name and full_name:
        parts = full_name.split(" ", 1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else ""
    status = _normalize_status(fields.get("status"))
    booking_date = _parse_iso(_first_non_empty(fields.get("booking_date"), fields.get("book_date"), fields.get("incarceration_date")))
    release_date = _parse_iso(_first_non_empty(fields.get("release_date"), fields.get("out_date")))
    bond_amount = _parse_float(_first_non_empty(fields.get("bond_amount"), fields.get("bond"), fields.get("total_bail"), fields.get("bail")))
    charges_text = _join_charges(
        _first_non_empty(fields.get("charges"), fields.get("charge"), fields.get("offense"), fields.get("description")),
        _first_non_empty(fields.get("charge_list")),
    )
    charge_rows = _charges_from_text(charges_text)
    bond_rows = [{"source_id": "b1", "amount": bond_amount, "type": "bond", "status": "set" if bond_amount is not None else "unknown"}]
    return {
        "state": "ID",
        "county": fields.get("county", ""),
        "facility": fields.get("facility", ""),
        "source_url": source_url,
        "source_type": fields.get("source_type", "custom_html"),
        "source_updated_at": _now_iso(),
        "inmate_id": _first_non_empty(fields.get("inmate_id"), fields.get("id")),
        "booking_number": _first_non_empty(fields.get("booking_number"), fields.get("booking_no"), fields.get("case_number"), fields.get("jail_id")),
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "dob": _parse_iso(_first_non_empty(fields.get("dob"), fields.get("date_of_birth"))),
        "age": int(fields["age"]) if str(fields.get("age", "")).strip().isdigit() else None,
        "sex": _first_non_empty(fields.get("sex"), fields.get("gender")),
        "race": _first_non_empty(fields.get("race")),
        "booking_date": booking_date,
        "release_date": release_date,
        "scheduled_release": _parse_iso(_first_non_empty(fields.get("scheduled_release"), fields.get("next_court_date"))),
        "charges": charge_rows,
        "status": status,
        "mugshot_url": _first_non_empty(fields.get("mugshot_url"), fields.get("photo")),
        "custody_level": _first_non_empty(fields.get("custody_level"), fields.get("classification")),
    }


def _fetch_html(url: str) -> bytes:
    _assert_authorized(url)
    headers = dict(REQUIRED_HEADERS)
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.content


def _fetch_pdf(url: str) -> bytes:
    _assert_authorized(url)
    headers = dict(REQUIRED_HEADERS)
    headers["Accept"] = "application/pdf,*/*;q=0.8"
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.content


def _stub_parse_html(source) -> List[Dict]:
    content = _fetch_html(source["source_url"])
    text = content.decode("utf-8", errors="ignore")[:10000]
    records = []
    if "No public roster" in text or "no online inmate roster" in text.lower():
        return records
    records.append(_parse_common_text_record({
        "county": source["county"],
        "facility": source["facility_name"],
        "source_type": "custom_html",
        "name": "HTML Parse Placeholder",
        "booking_number": "HTML-PLACEHOLDER",
        "status": "in_custody", "visibility": "public",
        "booking_date": datetime.now(timezone.utc).isoformat(),
    }, source["source_url"]))
    return records


def _stub_parse_pdf(source) -> List[Dict]:
    content = _fetch_pdf(source["source_url"])
    records = []
    records.append(_parse_common_text_record({
        "county": source["county"],
        "facility": source["facility_name"],
        "source_type": "pdf",
        "name": "PDF Parse Placeholder",
        "booking_number": "PDF-PLACEHOLDER",
        "status": "in_custody", "visibility": "public",
        "booking_date": datetime.now(timezone.utc).isoformat(),
    }, source["source_url"]))
    return records


def idaho_html(source) -> List[Dict]:
    return _stub_parse_html(source)


def idaho_pdf(source) -> List[Dict]:
    return _stub_parse_pdf(source)


ADAPTERS = {
    "idaho_html": idaho_html,
    "idaho_pdf": idaho_pdf,
}
