from __future__ import annotations

import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from web3.middleware import ExtraDataToPOAMiddleware
from web3 import Web3


@dataclass(frozen=True)
class Settings:
    rpc_url: str
    db_path: str
    gamma_base_url: str


def load_settings() -> Settings:
    load_dotenv()
    rpc_url = os.getenv("RPC_URL", "").strip()
    if not rpc_url:
        raise RuntimeError("RPC_URL is required in .env")
    db_path = os.getenv("DB_PATH", "./data/indexer.db").strip()
    gamma_base_url = os.getenv("GAMMA_BASE_URL", "https://gamma-api.polymarket.com").strip()
    return Settings(rpc_url=rpc_url, db_path=db_path, gamma_base_url=gamma_base_url)


def build_web3(rpc_url: str) -> Web3:
    # Disable inherited proxy env to avoid local proxy misconfiguration.
    session = requests.Session()
    session.trust_env = False
    provider = Web3.HTTPProvider(rpc_url, session=session)
    w3 = Web3(provider)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3
