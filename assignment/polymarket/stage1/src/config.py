from __future__ import annotations

import os

from dotenv import load_dotenv
import requests
from web3 import Web3

from .constants import NetworkConfig


def load_config() -> NetworkConfig:
    load_dotenv()
    rpc_url = os.getenv("RPC_URL", "").strip()
    if not rpc_url:
        raise RuntimeError("RPC_URL is required in .env")
    gamma_base_url = os.getenv("GAMMA_BASE_URL", "https://gamma-api.polymarket.com").strip()
    return NetworkConfig(rpc_url=rpc_url, gamma_base_url=gamma_base_url)


def build_web3(rpc_url: str) -> Web3:
    session = requests.Session()
    session.trust_env = False
    provider = Web3.HTTPProvider(rpc_url, session=session)
    return Web3(provider)
