from __future__ import annotations

import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from ..db.schema import init_db
from ..db.store import (
    fetch_event_by_slug,
    fetch_market_by_slug,
    fetch_markets_for_event,
    fetch_trades_by_token,
    fetch_trades_for_market,
)

_CONN: sqlite3.Connection | None = None


def _int_qs(params: dict[str, list[str]], key: str, default: int | None = None) -> int | None:
    raw = params.get(key, [None])[0]
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _json(handler: BaseHTTPRequestHandler, status: int, payload: object) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _conn() -> sqlite3.Connection:
    if _CONN is None:
        raise RuntimeError("Database not initialized")
    return _CONN


def _trade_row_to_dict(row: sqlite3.Row) -> dict[str, object]:
    return {
        "trade_id": row["id"],
        "market_id": row["market_id"],
        "tx_hash": row["tx_hash"],
        "log_index": row["log_index"],
        "block_number": row["block_number"],
        "timestamp": row["timestamp"],
        "maker": row["maker"],
        "taker": row["taker"],
        "side": row["side"],
        "outcome": row["outcome"],
        "price": row["price"],
        "size": row["size"],
        "token_id": row["token_id"],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        parts = [p for p in path.split("/") if p]

        if len(parts) == 2 and parts[0] == "events":
            event = fetch_event_by_slug(_conn(), parts[1])
            if not event:
                _json(self, 404, {"detail": "event not found"})
                return
            data = {k: event[k] for k in event.keys() if k != "raw_json"}
            _json(self, 200, data)
            return

        if len(parts) == 3 and parts[0] == "events" and parts[2] == "markets":
            rows = fetch_markets_for_event(_conn(), parts[1])
            payload = [{k: row[k] for k in row.keys() if k != "raw_json"} for row in rows]
            _json(self, 200, payload)
            return

        if len(parts) == 2 and parts[0] == "markets":
            market = fetch_market_by_slug(_conn(), parts[1])
            if not market:
                _json(self, 404, {"detail": "market not found"})
                return
            _json(
                self,
                200,
                {
                    "market_id": market["id"],
                    "slug": market["slug"],
                    "condition_id": market["condition_id"],
                    "question_id": market["question_id"],
                    "oracle": market["oracle"],
                    "collateral_token": market["collateral_token"],
                    "yes_token_id": market["yes_token_id"],
                    "no_token_id": market["no_token_id"],
                    "status": market["status"],
                },
            )
            return

        if len(parts) == 3 and parts[0] == "markets" and parts[2] == "trades":
            market = fetch_market_by_slug(_conn(), parts[1])
            if not market:
                _json(self, 404, {"detail": "market not found"})
                return
            limit = max(1, min(1000, _int_qs(params, "limit", 100) or 100))
            cursor = max(0, _int_qs(params, "cursor", 0) or 0)
            from_block = _int_qs(params, "fromBlock")
            to_block = _int_qs(params, "toBlock")
            rows = fetch_trades_for_market(
                _conn(),
                int(market["id"]),
                limit=limit,
                cursor=cursor,
                from_block=from_block,
                to_block=to_block,
            )
            _json(self, 200, [_trade_row_to_dict(r) for r in rows])
            return

        if len(parts) == 3 and parts[0] == "tokens" and parts[2] == "trades":
            limit = max(1, min(1000, _int_qs(params, "limit", 100) or 100))
            cursor = max(0, _int_qs(params, "cursor", 0) or 0)
            from_block = _int_qs(params, "fromBlock")
            to_block = _int_qs(params, "toBlock")
            rows = fetch_trades_by_token(
                _conn(),
                token_id=parts[1],
                limit=limit,
                cursor=cursor,
                from_block=from_block,
                to_block=to_block,
            )
            _json(self, 200, [_trade_row_to_dict(r) for r in rows])
            return

        _json(self, 404, {"detail": "not found"})


def main() -> None:
    global _CONN
    parser = argparse.ArgumentParser(description="Run stage2 API server")
    parser.add_argument("--db", required=True, help="Path to sqlite db")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    _CONN = init_db(args.db)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
