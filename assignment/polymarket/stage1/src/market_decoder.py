from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.types import TxReceipt

from .config import build_web3, load_config
from .constants import USDC_E
from .ctf.derive import derive_binary_positions, derive_condition_id
from .indexer.gamma import fetch_market_by_slug

DEFAULT_UMA_ORACLE = "0x157Ce2d672854c848c9b79C49a8Cc6cc89176a49"

CONDITION_PREPARATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "conditionId", "type": "bytes32"},
        {"indexed": True, "name": "oracle", "type": "address"},
        {"indexed": True, "name": "questionId", "type": "bytes32"},
        {"indexed": False, "name": "outcomeSlotCount", "type": "uint256"},
    ],
    "name": "ConditionPreparation",
    "type": "event",
}


def _write_output(path: str, data: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _extract_gamma_token_ids(gamma_market: dict[str, Any] | None) -> list[str]:
    if not gamma_market:
        return []
    raw = gamma_market.get("clobTokenIds")
    if isinstance(raw, list):
        return [str(v) for v in raw]
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed]
            except json.JSONDecodeError:
                pass
        pieces = [part.strip() for part in raw.split(",")]
        return [part for part in pieces if part]
    tokens = gamma_market.get("tokens")
    if isinstance(tokens, list):
        out: list[str] = []
        for token in tokens:
            if not isinstance(token, dict):
                continue
            for key in ("tokenId", "token_id", "id"):
                value = token.get(key)
                if value is not None:
                    out.append(str(value))
                    break
        return out
    return []


def _coalesce_dict_value(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def decode_condition_preparation(
    w3: Web3,
    tx_hash: str,
    log_index: int | None = None,
) -> dict[str, Any]:
    receipt: TxReceipt = w3.eth.get_transaction_receipt(tx_hash)
    contract = w3.eth.contract(abi=[CONDITION_PREPARATION_EVENT_ABI])
    event_decoder = contract.events.ConditionPreparation()
    parsed_logs: list[dict[str, Any]] = []
    for log in receipt["logs"]:
        if log_index is not None and int(log["logIndex"]) != log_index:
            continue
        try:
            evt = event_decoder.process_log(log)
        except Exception:
            continue
        args = evt["args"]
        parsed_logs.append(
            {
                "conditionId": Web3.to_hex(args["conditionId"]),
                "oracle": Web3.to_checksum_address(args["oracle"]),
                "questionId": Web3.to_hex(args["questionId"]),
                "outcomeSlotCount": int(args["outcomeSlotCount"]),
            }
        )
    if not parsed_logs:
        raise RuntimeError("ConditionPreparation log not found in the provided tx")
    return parsed_logs[0]


def decode_market(
    w3: Web3,
    condition_id: str,
    oracle: str,
    question_id: str,
    outcome_slot_count: int = 2,
    collateral_token: str = USDC_E,
    gamma_market: dict[str, Any] | None = None,
) -> dict[str, Any]:
    condition_verified = False
    if Web3.is_address(oracle) and question_id.startswith("0x"):
        derived_condition = derive_condition_id(oracle, question_id, outcome_slot_count)
        condition_verified = derived_condition.lower() == condition_id.lower()

    positions = derive_binary_positions(
        w3=w3,
        condition_id=condition_id,
        collateral_token=collateral_token,
    )
    yes_token_id = positions.position_yes
    no_token_id = positions.position_no

    gamma_token_ids = set(_extract_gamma_token_ids(gamma_market))
    token_match = bool(gamma_token_ids) and {yes_token_id, no_token_id}.issubset(gamma_token_ids)

    result: dict[str, Any] = {
        "conditionId": condition_id,
        "oracle": Web3.to_checksum_address(oracle),
        "questionId": question_id,
        "outcomeSlotCount": int(outcome_slot_count),
        "collateralToken": Web3.to_checksum_address(collateral_token),
        "yesTokenId": yes_token_id,
        "noTokenId": no_token_id,
        "gamma": {
            "market": gamma_market,
            "tokenIdsMatch": token_match,
            "conditionIdVerified": condition_verified,
        },
    }
    return result


def decode_market_from_slug(w3: Web3, gamma_base_url: str, market_slug: str) -> dict[str, Any]:
    gamma_market = fetch_market_by_slug(gamma_base_url, market_slug)
    if not gamma_market:
        raise RuntimeError(f"Market not found by slug: {market_slug}")

    condition_id = str(_coalesce_dict_value(gamma_market, ("conditionId", "condition_id")))
    question_id = str(_coalesce_dict_value(gamma_market, ("questionId", "question_id", "questionID")))
    oracle = _coalesce_dict_value(gamma_market, ("oracle", "oracleAddress", "oracle_address"))
    if not oracle or not Web3.is_address(str(oracle)):
        # Current Gamma payload may omit oracle; default to UMA adapter used by Polymarket.
        oracle = DEFAULT_UMA_ORACLE
    outcome_slot_count = int(_coalesce_dict_value(gamma_market, ("outcomeSlotCount", "outcome_slot_count")) or 2)

    return decode_market(
        w3=w3,
        condition_id=condition_id,
        oracle=str(oracle),
        question_id=question_id,
        outcome_slot_count=outcome_slot_count,
        collateral_token=USDC_E,
        gamma_market=gamma_market,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode Polymarket market params and token IDs")
    parser.add_argument("--market-slug", help="Gamma market slug")
    parser.add_argument("--tx-hash", help="ConditionPreparation transaction hash")
    parser.add_argument("--log-index", type=int, help="Optional log index inside tx")
    parser.add_argument("--output", help="Optional output json path")
    args = parser.parse_args()

    if not args.market_slug and not args.tx_hash:
        raise RuntimeError("Provide --market-slug or --tx-hash")

    config = load_config()
    w3 = build_web3(config.rpc_url)

    if args.market_slug:
        result = decode_market_from_slug(w3, config.gamma_base_url, args.market_slug)
    else:
        prepared = decode_condition_preparation(w3, args.tx_hash, args.log_index)
        result = decode_market(
            w3=w3,
            condition_id=prepared["conditionId"],
            oracle=prepared["oracle"],
            question_id=prepared["questionId"],
            outcome_slot_count=prepared["outcomeSlotCount"],
            collateral_token=USDC_E,
        )

    if args.output:
        _write_output(args.output, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
