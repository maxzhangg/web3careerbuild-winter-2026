from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_event(conn: sqlite3.Connection, event: dict[str, Any]) -> int:
    slug = str(event.get("slug") or "")
    title = event.get("title")
    status = "closed" if event.get("closed") else "active"
    created_at = event.get("createdAt") or _now_iso()
    raw_json = json.dumps(event, ensure_ascii=False)
    conn.execute(
        """
        INSERT INTO events(slug, title, status, created_at, raw_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
          title=excluded.title,
          status=excluded.status,
          created_at=excluded.created_at,
          raw_json=excluded.raw_json
        """,
        (slug, title, status, created_at, raw_json),
    )
    row = conn.execute("SELECT id FROM events WHERE slug = ?", (slug,)).fetchone()
    assert row is not None
    return int(row["id"])


def upsert_market(conn: sqlite3.Connection, market: dict[str, Any]) -> int:
    conn.execute(
        """
        INSERT INTO markets(
          event_id, slug, condition_id, question_id, oracle, collateral_token, yes_token_id, no_token_id,
          enable_neg_risk, status, created_at, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(condition_id) DO UPDATE SET
          event_id=excluded.event_id,
          slug=excluded.slug,
          question_id=excluded.question_id,
          oracle=excluded.oracle,
          collateral_token=excluded.collateral_token,
          yes_token_id=excluded.yes_token_id,
          no_token_id=excluded.no_token_id,
          enable_neg_risk=excluded.enable_neg_risk,
          status=excluded.status,
          created_at=excluded.created_at,
          raw_json=excluded.raw_json
        """,
        (
            market.get("event_id"),
            market["slug"],
            market["condition_id"],
            market.get("question_id"),
            market.get("oracle"),
            market["collateral_token"],
            market["yes_token_id"],
            market["no_token_id"],
            int(bool(market.get("enable_neg_risk"))),
            market.get("status"),
            market.get("created_at"),
            json.dumps(market.get("raw_json") or {}, ensure_ascii=False),
        ),
    )
    row = conn.execute("SELECT id FROM markets WHERE condition_id = ?", (market["condition_id"],)).fetchone()
    assert row is not None
    return int(row["id"])


def fetch_market_by_slug(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM markets WHERE slug = ?", (slug,)).fetchone()


def fetch_market_by_token_id(conn: sqlite3.Connection, token_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM markets WHERE yes_token_id = ? OR no_token_id = ?",
        (token_id, token_id),
    ).fetchone()


def fetch_event_by_slug(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM events WHERE slug = ?", (slug,)).fetchone()


def fetch_markets_for_event(conn: sqlite3.Connection, event_slug: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT m.* FROM markets m
        JOIN events e ON m.event_id = e.id
        WHERE e.slug = ?
        ORDER BY m.id ASC
        """,
        (event_slug,),
    ).fetchall()


def insert_trades(conn: sqlite3.Connection, trades: list[dict[str, Any]]) -> int:
    if not trades:
        return 0
    inserted = 0
    for t in trades:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO trades(
              market_id, tx_hash, log_index, block_number, timestamp, maker, taker,
              side, outcome, price, size, token_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                t["market_id"],
                t["tx_hash"],
                t["log_index"],
                t["block_number"],
                t["timestamp"],
                t["maker"],
                t["taker"],
                t["side"],
                t["outcome"],
                t["price"],
                t["size"],
                t["token_id"],
            ),
        )
        if cur.rowcount > 0:
            inserted += 1
    return inserted


def fetch_trades_for_market(
    conn: sqlite3.Connection,
    market_id: int,
    limit: int = 100,
    cursor: int = 0,
    from_block: int | None = None,
    to_block: int | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM trades WHERE market_id = ?"
    params: list[Any] = [market_id]
    if from_block is not None:
        query += " AND block_number >= ?"
        params.append(from_block)
    if to_block is not None:
        query += " AND block_number <= ?"
        params.append(to_block)
    query += " ORDER BY block_number DESC, log_index DESC LIMIT ? OFFSET ?"
    params.extend([limit, cursor])
    return conn.execute(query, tuple(params)).fetchall()


def fetch_trades_by_token(
    conn: sqlite3.Connection,
    token_id: str,
    limit: int = 100,
    cursor: int = 0,
    from_block: int | None = None,
    to_block: int | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM trades WHERE token_id = ?"
    params: list[Any] = [token_id]
    if from_block is not None:
        query += " AND block_number >= ?"
        params.append(from_block)
    if to_block is not None:
        query += " AND block_number <= ?"
        params.append(to_block)
    query += " ORDER BY block_number DESC, log_index DESC LIMIT ? OFFSET ?"
    params.extend([limit, cursor])
    return conn.execute(query, tuple(params)).fetchall()


def get_last_block(conn: sqlite3.Connection, key: str) -> int | None:
    row = conn.execute("SELECT last_block FROM sync_state WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return int(row["last_block"])


def set_last_block(conn: sqlite3.Connection, key: str, last_block: int) -> None:
    conn.execute(
        """
        INSERT INTO sync_state(key, last_block, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
          last_block=excluded.last_block,
          updated_at=excluded.updated_at
        """,
        (key, int(last_block), _now_iso()),
    )
