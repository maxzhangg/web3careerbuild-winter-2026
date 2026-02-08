from __future__ import annotations

from dataclasses import dataclass

from web3 import Web3

from ..constants import CONDITIONAL_TOKENS

_GET_COLLECTION_ID_ABI = {
    "name": "getCollectionId",
    "type": "function",
    "stateMutability": "pure",
    "inputs": [
        {"name": "parentCollectionId", "type": "bytes32"},
        {"name": "conditionId", "type": "bytes32"},
        {"name": "indexSet", "type": "uint256"},
    ],
    "outputs": [{"name": "", "type": "bytes32"}],
}

_GET_POSITION_ID_ABI = {
    "name": "getPositionId",
    "type": "function",
    "stateMutability": "pure",
    "inputs": [
        {"name": "collateralToken", "type": "address"},
        {"name": "collectionId", "type": "bytes32"},
    ],
    "outputs": [{"name": "", "type": "uint256"}],
}


@dataclass(frozen=True)
class BinaryPositions:
    condition_id: str
    collection_yes: str
    collection_no: str
    position_yes: str
    position_no: str


def derive_condition_id(oracle: str, question_id: str, outcome_slot_count: int) -> str:
    return Web3.solidity_keccak(
        ["address", "bytes32", "uint256"],
        [Web3.to_checksum_address(oracle), question_id, outcome_slot_count],
    ).hex()


def derive_binary_positions(
    w3: Web3,
    condition_id: str,
    collateral_token: str,
    conditional_tokens_address: str = CONDITIONAL_TOKENS,
) -> BinaryPositions:
    ct = w3.eth.contract(
        address=Web3.to_checksum_address(conditional_tokens_address),
        abi=[_GET_COLLECTION_ID_ABI, _GET_POSITION_ID_ABI],
    )
    parent = bytes(32)
    cid = Web3.to_bytes(hexstr=condition_id)
    collection_yes = ct.functions.getCollectionId(parent, cid, 1).call()
    collection_no = ct.functions.getCollectionId(parent, cid, 2).call()
    position_yes = ct.functions.getPositionId(
        Web3.to_checksum_address(collateral_token),
        collection_yes,
    ).call()
    position_no = ct.functions.getPositionId(
        Web3.to_checksum_address(collateral_token),
        collection_no,
    ).call()

    return BinaryPositions(
        condition_id=condition_id,
        collection_yes=Web3.to_hex(collection_yes),
        collection_no=Web3.to_hex(collection_no),
        position_yes=str(position_yes),
        position_no=str(position_no),
    )
