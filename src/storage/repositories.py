"""Repositorios para escrituras/lecturas principales de persistencia."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal

from src.models.schemas import NormalizedOdds, RawOddsCapture, SurebetOpportunity


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class RawCaptureRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_if_new(self, capture: RawOddsCapture) -> int | None:
        sql = """
        INSERT OR IGNORE INTO raw_odds_captures (
            bookmaker, source_event_id, fetched_at_utc, payload_json,
            payload_hash, collector_version, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cur = self.conn.execute(
            sql,
            (
                capture.bookmaker,
                capture.source_event_id,
                _iso(capture.fetched_at_utc),
                capture.payload_json,
                capture.payload_hash,
                capture.collector_version,
                _iso(capture.created_at_utc),
            ),
        )
        self.conn.commit()
        return cur.lastrowid or None


class NormalizedOddsRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert(self, odds: NormalizedOdds) -> int:
        sql = """
        INSERT INTO normalized_odds (
            capture_id, bookmaker, canonical_event_key, sport, league,
            home_team, away_team, event_start_utc, market_type,
            selection, line_value, odds_decimal, normalized_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cur = self.conn.execute(
            sql,
            (
                odds.capture_id,
                odds.bookmaker,
                odds.canonical_event_key,
                odds.sport,
                odds.league,
                odds.home_team,
                odds.away_team,
                _iso(odds.event_start_utc),
                odds.market_type,
                odds.selection,
                odds.line_value,
                str(odds.odds_decimal),
                _iso(odds.normalized_at_utc),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)


class SurebetRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_or_ignore(self, surebet: SurebetOpportunity) -> int | None:
        sql = """
        INSERT OR IGNORE INTO surebet_opportunities (
            opportunity_key, canonical_event_key, market_type,
            implied_probability_sum, expected_roi_percent,
            stake_plan_json, legs_json, detected_at_utc,
            status, validated_at_utc, expires_at_utc, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cur = self.conn.execute(
            sql,
            (
                surebet.opportunity_key,
                surebet.canonical_event_key,
                surebet.market_type,
                str(surebet.implied_probability_sum),
                str(surebet.expected_roi_percent),
                surebet.stake_plan_json,
                surebet.legs_json,
                _iso(surebet.detected_at_utc),
                surebet.status,
                _iso(surebet.validated_at_utc),
                _iso(surebet.expires_at_utc),
                surebet.notes,
            ),
        )
        self.conn.commit()
        return cur.lastrowid or None

    def mark_status(self, opportunity_key: str, status: str) -> None:
        self.conn.execute(
            "UPDATE surebet_opportunities SET status = ? WHERE opportunity_key = ?",
            (status, opportunity_key),
        )
        self.conn.commit()


def serialize_dataclass(instance: object) -> str:
    """Útil para logging/debug de objetos de modelo."""

    def converter(value: object) -> str:
        if isinstance(value, (datetime, Decimal)):
            return str(value)
        raise TypeError(f"No serializable type: {type(value)!r}")

    return json.dumps(asdict(instance), default=converter, ensure_ascii=False)
