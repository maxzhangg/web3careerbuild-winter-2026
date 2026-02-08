from __future__ import annotations

from typing import Any

import requests

_SESSION = requests.Session()
_SESSION.trust_env = False


def _get(url: str, params: dict[str, Any] | None = None) -> Any:
    response = _SESSION.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_market_by_slug(base_url: str, slug: str) -> dict[str, Any] | None:
    payload = _get(f"{base_url.rstrip('/')}/markets", params={"slug": slug})
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict) and payload.get("slug") == slug:
        return payload
    return None


def fetch_event_by_slug(base_url: str, slug: str) -> dict[str, Any] | None:
    payload = _get(f"{base_url.rstrip('/')}/events", params={"slug": slug})
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict) and payload.get("slug") == slug:
        return payload
    return None


def fetch_market_by_condition_or_tokens(
    base_url: str,
    condition_id: str | None = None,
    token_ids: list[str] | None = None,
) -> dict[str, Any] | None:
    if condition_id:
        payload = _get(f"{base_url.rstrip('/')}/markets", params={"conditionId": condition_id})
        if isinstance(payload, list) and payload:
            return payload[0]
    if token_ids:
        for token_id in token_ids:
            payload = _get(f"{base_url.rstrip('/')}/markets", params={"clob_token_ids": token_id})
            if isinstance(payload, list) and payload:
                return payload[0]
    return None
