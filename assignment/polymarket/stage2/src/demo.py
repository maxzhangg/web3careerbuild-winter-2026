from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import build_web3, load_settings
from .db.schema import init_db, reset_db
from .db.store import fetch_market_by_slug, fetch_trades_for_market
from .indexer.run import run_indexer


def _write_json(path: str, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _row_to_trade(row: Any) -> dict[str, Any]:
    return {
        "tx_hash": row["tx_hash"],
        "log_index": row["log_index"],
        "block_number": row["block_number"],
        "timestamp": row["timestamp"],
        "side": row["side"],
        "outcome": row["outcome"],
        "price": row["price"],
        "size": row["size"],
        "token_id": row["token_id"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run stage2 polymarket indexer demo")
    parser.add_argument("--tx-hash", help="Use tx block as from/to block")
    parser.add_argument("--from-block", type=int, help="Start block for indexing")
    parser.add_argument("--to-block", type=int, help="End block for indexing")
    parser.add_argument("--event-slug", required=True, help="Gamma event slug for market discovery")
    parser.add_argument("--db", help="SQLite DB path")
    parser.add_argument("--reset-db", action="store_true", help="Delete DB before running")
    parser.add_argument("--output", help="Write output json to file")
    args = parser.parse_args()

    settings = load_settings()
    db_path = args.db or settings.db_path or "./data/demo_indexer.db"
    w3 = build_web3(settings.rpc_url)
    conn = init_db(db_path)
    if args.reset_db:
        reset_db(conn)
        conn.close()
        conn = init_db(db_path)

    from_block = args.from_block
    to_block = args.to_block
    if args.tx_hash:
        tx = w3.eth.get_transaction(args.tx_hash)
        tx_block = int(tx["blockNumber"])
        from_block = tx_block if from_block is None else from_block
        to_block = tx_block if to_block is None else to_block
    if from_block is None or to_block is None:
        raise RuntimeError("Provide --tx-hash or both --from-block and --to-block")

    summary = run_indexer(
        w3=w3,
        conn=conn,
        gamma_base_url=settings.gamma_base_url,
        from_block=from_block,
        to_block=to_block,
        event_slug=args.event_slug,
    )
    market = fetch_market_by_slug(conn, summary["market_slug"])
    market_id = int(market["id"]) if market else summary["market_id"]
    sample_rows = fetch_trades_for_market(conn, market_id, limit=10, cursor=0) if market_id else []
    sample_trades = [_row_to_trade(row) for row in sample_rows]

    output = {
        "stage2": {
            "from_block": summary["from_block"],
            "to_block": summary["to_block"],
            "inserted_trades": summary["inserted_trades"],
            "market_slug": summary["market_slug"],
            "market_id": summary["market_id"],
            "sample_trades": sample_trades,
            "db_path": db_path,
        }
    }
    if args.output:
        _write_json(args.output, output)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
