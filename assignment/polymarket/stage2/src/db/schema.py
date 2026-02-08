from __future__ import annotations

import sqlite3
from pathlib import Path


def init_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.executescript(
        """
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          slug TEXT NOT NULL UNIQUE,
          title TEXT,
          status TEXT,
          created_at TEXT,
          raw_json TEXT
        );

        CREATE TABLE IF NOT EXISTS markets (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id INTEGER,
          slug TEXT NOT NULL UNIQUE,
          condition_id TEXT NOT NULL UNIQUE,
          question_id TEXT,
          oracle TEXT,
          collateral_token TEXT NOT NULL,
          yes_token_id TEXT NOT NULL,
          no_token_id TEXT NOT NULL,
          enable_neg_risk INTEGER NOT NULL DEFAULT 0,
          status TEXT,
          created_at TEXT,
          raw_json TEXT,
          FOREIGN KEY (event_id) REFERENCES events(id)
        );

        CREATE TABLE IF NOT EXISTS trades (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          market_id INTEGER NOT NULL,
          tx_hash TEXT NOT NULL,
          log_index INTEGER NOT NULL,
          block_number INTEGER NOT NULL,
          timestamp TEXT NOT NULL,
          maker TEXT NOT NULL,
          taker TEXT NOT NULL,
          side TEXT NOT NULL,
          outcome TEXT NOT NULL,
          price TEXT NOT NULL,
          size TEXT NOT NULL,
          token_id TEXT NOT NULL,
          UNIQUE (tx_hash, log_index),
          FOREIGN KEY (market_id) REFERENCES markets(id)
        );

        CREATE INDEX IF NOT EXISTS idx_trades_market_id ON trades(market_id);
        CREATE INDEX IF NOT EXISTS idx_trades_token_id ON trades(token_id);
        CREATE INDEX IF NOT EXISTS idx_trades_block_number ON trades(block_number);

        CREATE TABLE IF NOT EXISTS sync_state (
          key TEXT PRIMARY KEY,
          last_block INTEGER NOT NULL,
          updated_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    return conn


def reset_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS trades;
        DROP TABLE IF EXISTS markets;
        DROP TABLE IF EXISTS events;
        DROP TABLE IF EXISTS sync_state;
        """
    )
    conn.commit()
