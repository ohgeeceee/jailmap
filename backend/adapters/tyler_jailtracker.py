from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List

from backend.adapters.idaho import AdapterResult


def fetch(source) -> AdapterResult:
    """Stub adapter for Tyler JailTracker (Blazor WASM SPA).

    JailTracker pages make runtime API calls via JavaScript that aren't
    easily replicated with httpx. This stub returns empty so the
    jurisdiction is registered (staging_only) while a proper adapter
    or manual discovery path is built. See notes column for the roster URL.
    """
    print(f"  Tyler JailTracker stub: {source['county']} — needs Playwright-based adapter or manual URL discovery")
    return AdapterResult(source, [])
