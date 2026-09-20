from __future__ import annotations

import random
import time
from urllib.parse import urlparse

import httpx


class ResilientHttpClient:
    """Bounded retries and polite per-client throttling for public roster endpoints."""

    RETRYABLE = {429, 500, 502, 503, 504}

    def __init__(self, *, min_interval_seconds: float = 1.0, max_attempts: int = 4) -> None:
        self.min_interval = max(0.0, min_interval_seconds)
        self.max_attempts = min(max(1, max_attempts), 6)
        self.last_request_at = 0.0
        self.client = httpx.Client(
            timeout=httpx.Timeout(30.0), follow_redirects=True,
            headers={"User-Agent": "JailMapRosterIndexer/1.0 (+https://jailmap.com/contact)"},
        )

    def get(self, url: str, **kwargs):
        if urlparse(url).scheme not in {"http", "https"}:
            raise ValueError("source URL must use HTTP or HTTPS")
        response = None
        for attempt in range(self.max_attempts):
            delay = self.min_interval - (time.monotonic() - self.last_request_at)
            if delay > 0:
                time.sleep(delay)
            response = self.client.get(url, **kwargs)
            self.last_request_at = time.monotonic()
            if response.status_code not in self.RETRYABLE or attempt == self.max_attempts - 1:
                return response
            retry_after = response.headers.get("Retry-After")
            wait = min(float(retry_after), 30.0) if retry_after and retry_after.isdigit() else min(2 ** attempt + random.random(), 30.0)
            time.sleep(wait)
        return response

    def close(self) -> None:
        self.client.close()
