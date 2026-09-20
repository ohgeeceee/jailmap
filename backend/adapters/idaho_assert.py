def _assert_authorized(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("Source endpoint is not authorized")
    hostname = parsed.hostname or ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if ALLOWED_HOSTS and hostname not in ALLOWED_HOSTS:
        raise ValueError("Source endpoint host is not allowed")