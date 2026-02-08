from __future__ import annotations

from typing import Any

import requests

_SESSION = requests.Session()
_SESSION.trust_env = False


def _get(url: str, params: dict[str, Any] | None = None) -> Any:
    response = _SESSION.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_event_by_slug(base_url: str, slug: str) -> dict[str, Any] | None:
    payload = _get(f"{base_url.rstrip('/')}/events", params={"slug": slug})
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict) and payload.get("slug") == slug:
        return payload
    return None


def fetch_market_by_slug(base_url: str, slug: str) -> dict[str, Any] | None:
    payload = _get(f"{base_url.rstrip('/')}/markets", params={"slug": slug})
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict) and payload.get("slug") == slug:
        return payload
    return None


def fetch_markets_by_event_slug(base_url: str, event_slug: str) -> list[dict[str, Any]]:
    event = fetch_event_by_slug(base_url, event_slug)
    if not event:
        return []
    markets = event.get("markets")
    if isinstance(markets, list):
        return [m for m in markets if isinstance(m, dict)]
    market = fetch_market_by_slug(base_url, event_slug)
    return [market] if market else []
