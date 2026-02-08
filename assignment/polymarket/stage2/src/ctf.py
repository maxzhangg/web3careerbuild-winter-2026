from __future__ import annotations

from web3 import Web3

from .constants import CONDITIONAL_TOKENS

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


def derive_yes_no_token_ids(
    w3: Web3,
    condition_id: str,
    collateral_token: str,
    conditional_tokens_address: str = CONDITIONAL_TOKENS,
) -> tuple[str, str]:
    ct = w3.eth.contract(
        address=Web3.to_checksum_address(conditional_tokens_address),
        abi=[_GET_COLLECTION_ID_ABI, _GET_POSITION_ID_ABI],
    )
    parent = bytes(32)
    cid = Web3.to_bytes(hexstr=condition_id)
    collection_yes = ct.functions.getCollectionId(parent, cid, 1).call()
    collection_no = ct.functions.getCollectionId(parent, cid, 2).call()
    yes = ct.functions.getPositionId(Web3.to_checksum_address(collateral_token), collection_yes).call()
    no = ct.functions.getPositionId(Web3.to_checksum_address(collateral_token), collection_no).call()
    return str(yes), str(no)
