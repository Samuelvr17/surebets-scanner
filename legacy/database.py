"""Persistencia SQLite local para el scanner.

Decisión técnica: SQLite en modo WAL para empezar sin servidores externos,
con integridad transaccional y buen rendimiento para escritura/lectura local.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/surebets.db")


SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_odds_captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bookmaker TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    fetched_at_utc TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    collector_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    UNIQUE(bookmaker, payload_hash)
);

CREATE INDEX IF NOT EXISTS idx_raw_bookmaker_fetched
ON raw_odds_captures(bookmaker, fetched_at_utc DESC);

CREATE TABLE IF NOT EXISTS normalized_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capture_id INTEGER NOT NULL,
    bookmaker TEXT NOT NULL,
    canonical_event_key TEXT NOT NULL,
    sport TEXT NOT NULL,
    league TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    event_start_utc TEXT NOT NULL,
    market_type TEXT NOT NULL,
    selection TEXT NOT NULL,
    line_value TEXT,
    odds_decimal TEXT NOT NULL,
    normalized_at_utc TEXT NOT NULL,
    FOREIGN KEY(capture_id) REFERENCES raw_odds_captures(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_norm_event_market
ON normalized_odds(canonical_event_key, market_type, normalized_at_utc DESC);

CREATE TABLE IF NOT EXISTS surebet_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_key TEXT NOT NULL UNIQUE,
    canonical_event_key TEXT NOT NULL,
    market_type TEXT NOT NULL,
    implied_probability_sum TEXT NOT NULL,
    expected_roi_percent TEXT NOT NULL,
    stake_plan_json TEXT NOT NULL,
    legs_json TEXT NOT NULL,
    detected_at_utc TEXT NOT NULL,
    status TEXT NOT NULL,
    validated_at_utc TEXT,
    expires_at_utc TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_surebet_detected_status
ON surebet_opportunities(status, detected_at_utc DESC);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
