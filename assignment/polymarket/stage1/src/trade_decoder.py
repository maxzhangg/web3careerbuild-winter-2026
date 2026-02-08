from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.types import TxReceipt

from .config import build_web3, load_config
from .constants import CTF_EXCHANGE, NEG_RISK_EXCHANGE

ORDER_FILLED_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "orderHash", "type": "bytes32"},
        {"indexed": True, "name": "maker", "type": "address"},
        {"indexed": True, "name": "taker", "type": "address"},
        {"indexed": False, "name": "makerAssetId", "type": "uint256"},
        {"indexed": False, "name": "takerAssetId", "type": "uint256"},
        {"indexed": False, "name": "makerAmountFilled", "type": "uint256"},
        {"indexed": False, "name": "takerAmountFilled", "type": "uint256"},
        {"indexed": False, "name": "fee", "type": "uint256"},
    ],
    "name": "OrderFilled",
    "type": "event",
}


@dataclass(frozen=True)
class Trade:
    tx_hash: str
    log_index: int
    exchange: str
    maker: str
    taker: str
    maker_asset_id: str
    taker_asset_id: str
    maker_amount: str
    taker_amount: str
    price: str
    token_id: str
    side: str


def _decimal_str(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _decode_trade(raw: dict[str, Any], tx_hash: str, exchange: str, log_index: int) -> Trade | None:
    maker_asset_id = int(raw["makerAssetId"])
    taker_asset_id = int(raw["takerAssetId"])
    maker_amount = int(raw["makerAmountFilled"])
    taker_amount = int(raw["takerAmountFilled"])
    maker = Web3.to_checksum_address(raw["maker"])
    taker = Web3.to_checksum_address(raw["taker"])

    if maker_asset_id == 0 and taker_amount > 0:
        side = "BUY"
        token_id = taker_asset_id
        price = Decimal(maker_amount) / Decimal(taker_amount)
    elif taker_asset_id == 0 and maker_amount > 0:
        side = "SELL"
        token_id = maker_asset_id
        price = Decimal(taker_amount) / Decimal(maker_amount)
    else:
        return None

    return Trade(
        tx_hash=tx_hash,
        log_index=log_index,
        exchange=Web3.to_checksum_address(exchange),
        maker=maker,
        taker=taker,
        maker_asset_id=str(maker_asset_id),
        taker_asset_id=str(taker_asset_id),
        maker_amount=str(maker_amount),
        taker_amount=str(taker_amount),
        price=_decimal_str(price),
        token_id=str(token_id),
        side=side,
    )


def decode_trades_from_receipt(w3: Web3, receipt: TxReceipt) -> list[Trade]:
    exchange_set = {CTF_EXCHANGE.lower(), NEG_RISK_EXCHANGE.lower()}
    exchange_contract = w3.eth.contract(abi=[ORDER_FILLED_EVENT_ABI])
    decoder = exchange_contract.events.OrderFilled()
    results: list[Trade] = []
    for log in receipt["logs"]:
        if log["address"].lower() not in exchange_set:
            continue
        try:
            parsed = decoder.process_log(log)
        except Exception:
            continue
        args = parsed["args"]
        taker = Web3.to_checksum_address(args["taker"])
        exchange = Web3.to_checksum_address(log["address"])
        if taker.lower() == exchange.lower():
            continue
        trade = _decode_trade(
            raw=args,
            tx_hash=Web3.to_hex(receipt["transactionHash"]),
            exchange=exchange,
            log_index=int(log["logIndex"]),
        )
        if trade:
            results.append(trade)
    results.sort(key=lambda item: item.log_index)
    return results


def decode_trades(w3: Web3, tx_hash: str) -> list[Trade]:
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    return decode_trades_from_receipt(w3, receipt)


def _write_output(path: str, data: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode Polymarket OrderFilled logs from a tx hash")
    parser.add_argument("--tx-hash", required=True, help="Polygon transaction hash")
    parser.add_argument("--output", help="Optional output json path")
    args = parser.parse_args()

    config = load_config()
    w3 = build_web3(config.rpc_url)
    trades = [asdict(t) for t in decode_trades(w3, args.tx_hash)]

    if args.output:
        _write_output(args.output, trades)
    print(json.dumps(trades, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
