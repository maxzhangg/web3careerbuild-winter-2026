from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from web3 import Web3

from ..constants import CTF_EXCHANGE, DEFAULT_UMA_ORACLE, NEG_RISK_EXCHANGE, USDC_E
from ..ctf import derive_yes_no_token_ids
from ..db.store import (
    fetch_market_by_slug,
    fetch_market_by_token_id,
    insert_trades,
    set_last_block,
    upsert_event,
    upsert_market,
)
from ..decoder import DecodedTrade, ORDER_FILLED_EVENT_ABI, decode_order_filled_log
from ..gamma import fetch_event_by_slug, fetch_markets_by_event_slug


def _parse_clob_token_ids(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(v) for v in raw]
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed]
            except json.JSONDecodeError:
                pass
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def discover_markets(
    w3: Web3,
    conn: sqlite3.Connection,
    gamma_base_url: str,
    event_slug: str,
) -> list[int]:
    event = fetch_event_by_slug(gamma_base_url, event_slug)
    if not event:
        return []
    event_id = upsert_event(conn, event)
    markets = fetch_markets_by_event_slug(gamma_base_url, event_slug)
    market_ids: list[int] = []
    for market in markets:
        condition_id = str(market.get("conditionId") or "")
        if not condition_id:
            continue
        yes_id, no_id = derive_yes_no_token_ids(w3, condition_id=condition_id, collateral_token=USDC_E)
        gamma_token_ids = _parse_clob_token_ids(market.get("clobTokenIds"))
        if len(gamma_token_ids) == 2:
            # Keep on-chain derived IDs authoritative but require that Gamma includes both.
            if not {yes_id, no_id}.issubset(set(gamma_token_ids)):
                continue

        question_id = market.get("questionID") or market.get("questionId") or market.get("question_id")
        market_record = {
            "event_id": event_id,
            "slug": str(market.get("slug") or condition_id),
            "condition_id": condition_id,
            "question_id": str(question_id) if question_id else None,
            "oracle": str(market.get("oracleAddress") or market.get("oracle") or DEFAULT_UMA_ORACLE),
            "collateral_token": USDC_E,
            "yes_token_id": yes_id,
            "no_token_id": no_id,
            "enable_neg_risk": bool(market.get("negRisk")) or bool(event.get("enableNegRisk")),
            "status": "closed" if market.get("closed") else "active",
            "created_at": market.get("createdAt") or datetime.now(timezone.utc).isoformat(),
            "raw_json": market,
        }
        market_ids.append(upsert_market(conn, market_record))
    conn.commit()
    return market_ids


def _block_timestamp_iso(w3: Web3, block_number: int, cache: dict[int, str]) -> str:
    if block_number in cache:
        return cache[block_number]
    block = w3.eth.get_block(block_number)
    ts = datetime.fromtimestamp(int(block["timestamp"]), tz=timezone.utc).replace(tzinfo=None).isoformat()
    cache[block_number] = ts
    return ts


def _to_trade_row(decoded: DecodedTrade, market_row: sqlite3.Row, timestamp: str) -> dict[str, Any]:
    outcome = "YES" if str(market_row["yes_token_id"]) == decoded.token_id else "NO"
    return {
        "market_id": int(market_row["id"]),
        "tx_hash": decoded.tx_hash,
        "log_index": decoded.log_index,
        "block_number": decoded.block_number,
        "timestamp": timestamp,
        "maker": decoded.maker,
        "taker": decoded.taker,
        "side": decoded.side,
        "outcome": outcome,
        "price": decoded.price,
        "size": decoded.size,
        "token_id": decoded.token_id,
    }


def run_indexer(
    w3: Web3,
    conn: sqlite3.Connection,
    gamma_base_url: str,
    from_block: int,
    to_block: int,
    event_slug: str,
) -> dict[str, Any]:
    discover_markets(w3, conn, gamma_base_url, event_slug)
    topic0 = Web3.to_hex(w3.keccak(text="OrderFilled(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)"))
    logs = w3.eth.get_logs(
        {
            "fromBlock": int(from_block),
            "toBlock": int(to_block),
            "address": [Web3.to_checksum_address(CTF_EXCHANGE), Web3.to_checksum_address(NEG_RISK_EXCHANGE)],
            "topics": [topic0],
        }
    )
    block_cache: dict[int, str] = {}
    rows: list[dict[str, Any]] = []
    for log in logs:
        decoded = decode_order_filled_log(w3, log)
        if not decoded:
            continue
        market_row = fetch_market_by_token_id(conn, decoded.token_id)
        if not market_row:
            # Best-effort refresh when token was not yet discovered.
            discover_markets(w3, conn, gamma_base_url, event_slug)
            market_row = fetch_market_by_token_id(conn, decoded.token_id)
        if not market_row:
            continue
        ts = _block_timestamp_iso(w3, decoded.block_number, block_cache)
        rows.append(_to_trade_row(decoded, market_row, ts))

    inserted = insert_trades(conn, rows)
    set_last_block(conn, "trade_sync", int(to_block))
    conn.commit()

    market = fetch_market_by_slug(conn, event_slug)
    if not market:
        mlist = conn.execute("SELECT * FROM markets ORDER BY id LIMIT 1").fetchone()
        market = mlist
    return {
        "from_block": int(from_block),
        "to_block": int(to_block),
        "inserted_trades": inserted,
        "market_slug": market["slug"] if market else event_slug,
        "market_id": int(market["id"]) if market else None,
    }
