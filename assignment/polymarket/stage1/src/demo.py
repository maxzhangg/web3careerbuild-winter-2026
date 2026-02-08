from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.types import TxReceipt

from .config import build_web3, load_config
from .indexer.gamma import fetch_event_by_slug
from .market_decoder import decode_market_from_slug
from .trade_decoder import decode_trades

POSITION_SPLIT_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "stakeholder", "type": "address"},
        {"indexed": False, "name": "collateralToken", "type": "address"},
        {"indexed": True, "name": "parentCollectionId", "type": "bytes32"},
        {"indexed": True, "name": "conditionId", "type": "bytes32"},
        {"indexed": False, "name": "partition", "type": "uint256[]"},
        {"indexed": False, "name": "amount", "type": "uint256"},
    ],
    "name": "PositionSplit",
    "type": "event",
}


def _write_output(path: str, data: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def decode_position_split(w3: Web3, receipt: TxReceipt) -> dict[str, Any] | None:
    contract = w3.eth.contract(abi=[POSITION_SPLIT_EVENT_ABI])
    decoder = contract.events.PositionSplit()
    for log in receipt["logs"]:
        try:
            parsed = decoder.process_log(log)
        except Exception:
            continue
        args = parsed["args"]
        return {
            "txHash": Web3.to_hex(receipt["transactionHash"]),
            "logIndex": int(log["logIndex"]),
            "stakeholder": Web3.to_checksum_address(args["stakeholder"]),
            "collateralToken": Web3.to_checksum_address(args["collateralToken"]),
            "parentCollectionId": Web3.to_hex(args["parentCollectionId"]),
            "conditionId": Web3.to_hex(args["conditionId"]),
            "partition": [int(v) for v in args["partition"]],
            "amount": str(int(args["amount"])),
        }
    return None


def _extract_first_market_slug(event: dict[str, Any] | None, fallback_slug: str) -> str:
    if not event:
        return fallback_slug
    markets = event.get("markets")
    if isinstance(markets, list) and markets:
        first = markets[0]
        if isinstance(first, dict) and first.get("slug"):
            return str(first["slug"])
    return fallback_slug


def main() -> None:
    parser = argparse.ArgumentParser(description="Run stage1 trade + market decode demo")
    parser.add_argument("--tx-hash", required=True, help="Transaction hash to decode")
    parser.add_argument("--event-slug", required=True, help="Gamma event slug")
    parser.add_argument("--output", help="Optional output file path")
    args = parser.parse_args()

    config = load_config()
    w3 = build_web3(config.rpc_url)

    trades = [t.__dict__ for t in decode_trades(w3, args.tx_hash)]
    receipt = w3.eth.get_transaction_receipt(args.tx_hash)
    split = decode_position_split(w3, receipt)

    gamma_event = fetch_event_by_slug(config.gamma_base_url, args.event_slug)
    market_slug = _extract_first_market_slug(gamma_event, args.event_slug)
    market = decode_market_from_slug(w3, config.gamma_base_url, market_slug)

    output = {
        "stage1": {
            "tx_hash": args.tx_hash,
            "trades": trades,
            "position_split": split,
            "market": {
                "conditionId": market["conditionId"],
                "oracle": market["oracle"],
                "questionId": market["questionId"],
                "collateralToken": market["collateralToken"],
                "yesTokenId": market["yesTokenId"],
                "noTokenId": market["noTokenId"],
            },
            "gamma": {
                "event": gamma_event,
                "market": market.get("gamma", {}).get("market"),
                "tokenIdsMatch": market.get("gamma", {}).get("tokenIdsMatch"),
            },
        }
    }

    if args.output:
        _write_output(args.output, output)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
