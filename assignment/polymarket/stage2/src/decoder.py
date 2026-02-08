from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from web3 import Web3

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
class DecodedTrade:
    tx_hash: str
    log_index: int
    block_number: int
    exchange: str
    maker: str
    taker: str
    maker_asset_id: str
    taker_asset_id: str
    maker_amount: str
    taker_amount: str
    token_id: str
    side: str
    price: str
    size: str


def _decimal_str(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def decode_order_filled_log(w3: Web3, log: dict[str, Any]) -> DecodedTrade | None:
    if log["address"].lower() not in {CTF_EXCHANGE.lower(), NEG_RISK_EXCHANGE.lower()}:
        return None
    contract = w3.eth.contract(abi=[ORDER_FILLED_EVENT_ABI])
    decoder = contract.events.OrderFilled()
    try:
        parsed = decoder.process_log(log)
    except Exception:
        return None

    args = parsed["args"]
    exchange = Web3.to_checksum_address(log["address"])
    maker = Web3.to_checksum_address(args["maker"])
    taker = Web3.to_checksum_address(args["taker"])
    if taker.lower() == exchange.lower():
        return None

    maker_asset_id = int(args["makerAssetId"])
    taker_asset_id = int(args["takerAssetId"])
    maker_amount = int(args["makerAmountFilled"])
    taker_amount = int(args["takerAmountFilled"])

    if maker_asset_id == 0 and taker_amount > 0:
        side = "BUY"
        token_id = taker_asset_id
        price = Decimal(maker_amount) / Decimal(taker_amount)
        size = Decimal(taker_amount) / Decimal(10**6)
    elif taker_asset_id == 0 and maker_amount > 0:
        side = "SELL"
        token_id = maker_asset_id
        price = Decimal(taker_amount) / Decimal(maker_amount)
        size = Decimal(maker_amount) / Decimal(10**6)
    else:
        return None

    return DecodedTrade(
        tx_hash=Web3.to_hex(log["transactionHash"]),
        log_index=int(log["logIndex"]),
        block_number=int(log["blockNumber"]),
        exchange=exchange,
        maker=maker,
        taker=taker,
        maker_asset_id=str(maker_asset_id),
        taker_asset_id=str(taker_asset_id),
        maker_amount=str(maker_amount),
        taker_amount=str(taker_amount),
        token_id=str(token_id),
        side=side,
        price=_decimal_str(price),
        size=_decimal_str(size),
    )
