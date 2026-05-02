"""Normalización estricta de payloads crudos a formato canónico.

Reglas clave:
- Nombres (equipos/ligas) vía tabla de aliases externa editable en JSON.
- Hora del evento siempre convertida a UTC.
- Mercado clasificado de forma estricta; si hay ambigüedad se descarta.
- Cuotas convertidas a decimal.
- Todo descarte queda auditado con motivo explícito.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DiscardedOdd:
    bookmaker: str
    source_event_id: str
    reason: str
    raw_odd: dict[str, Any]


@dataclass(slots=True)
class NormalizedOddRecord:
    bookmaker: str
    source_event_id: str
    league: str
    home_team: str
    away_team: str
    event_start_utc: datetime
    market_type: str
    selection: str
    line_value: str | None
    odds_decimal: Decimal


@dataclass(slots=True)
class NormalizationResult:
    normalized: list[NormalizedOddRecord]
    discarded: list[DiscardedOdd]


class OddsNormalizer:
    def __init__(self, aliases_file: Path | None = None) -> None:
        default_file = Path(__file__).with_name("aliases.json")
        self.aliases_file = aliases_file or default_file
        aliases = json.loads(self.aliases_file.read_text(encoding="utf-8"))
        self.team_aliases = {self._key(k): v for k, v in aliases.get("teams", {}).items()}
        self.league_aliases = {self._key(k): v for k, v in aliases.get("leagues", {}).items()}

    @staticmethod
    def _key(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower().strip()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        return re.sub(r"\s+", " ", normalized)

    def normalize_payload(self, bookmaker: str, source_event_id: str, payload: dict[str, Any]) -> NormalizationResult:
        discarded: list[DiscardedOdd] = []
        normalized: list[NormalizedOddRecord] = []

        home = self._normalize_alias(payload.get("home_team"), self.team_aliases)
        away = self._normalize_alias(payload.get("away_team"), self.team_aliases)
        league = self._normalize_alias(payload.get("league"), self.league_aliases)

        if not home or not away:
            return NormalizationResult(
                normalized=[],
                discarded=[DiscardedOdd(bookmaker, source_event_id, "unknown_team_alias", payload)],
            )
        if not league:
            return NormalizationResult(
                normalized=[],
                discarded=[DiscardedOdd(bookmaker, source_event_id, "unknown_league_alias", payload)],
            )

        event_start_utc = self._parse_utc(payload.get("event_start"))
        if not event_start_utc:
            return NormalizationResult(
                normalized=[],
                discarded=[DiscardedOdd(bookmaker, source_event_id, "invalid_event_start", payload)],
            )

        for odd in payload.get("odds", []):
            market_type = self._classify_market(odd)
            if not market_type:
                discarded.append(DiscardedOdd(bookmaker, source_event_id, "unknown_or_ambiguous_market", odd))
                continue

            decimal_odd = self._to_decimal_odd(odd.get("odds"))
            if decimal_odd is None:
                discarded.append(DiscardedOdd(bookmaker, source_event_id, "invalid_odds_format", odd))
                continue

            selection = str(odd.get("selection", "")).strip()
            if not selection:
                discarded.append(DiscardedOdd(bookmaker, source_event_id, "missing_selection", odd))
                continue

            normalized.append(
                NormalizedOddRecord(
                    bookmaker=bookmaker,
                    source_event_id=source_event_id,
                    league=league,
                    home_team=home,
                    away_team=away,
                    event_start_utc=event_start_utc,
                    market_type=market_type,
                    selection=selection,
                    line_value=str(odd.get("line")) if odd.get("line") is not None else None,
                    odds_decimal=decimal_odd,
                )
            )

        return NormalizationResult(normalized=normalized, discarded=discarded)

    def _normalize_alias(self, value: Any, alias_map: dict[str, str]) -> str | None:
        if not value:
            return None
        key = self._key(str(value))
        return alias_map.get(key)

    def _parse_utc(self, value: Any) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if dt.tzinfo is None:
            return None
        return dt.astimezone(UTC)

    def _classify_market(self, odd: dict[str, Any]) -> str | None:
        text = self._key(f"{odd.get('market', '')} {odd.get('selection', '')}")
        if any(k in text for k in ["1x2", "full time result", "match winner"]) and "handicap" not in text:
            return "MATCH_RESULT_1X2"
        if "asian handicap" in text:
            return "ASIAN_HANDICAP"
        if "over under" in text or "totals" in text:
            return "TOTALS"
        if "both teams to score" in text or "btts" in text:
            return "BTTS"
        return None

    def _to_decimal_odd(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, (int, float, Decimal, str)):
            s = str(value).strip()
            if not s:
                return None
            # fraccional "5/2" -> 3.5
            if "/" in s:
                parts = s.split("/")
                if len(parts) == 2:
                    try:
                        num = Decimal(parts[0])
                        den = Decimal(parts[1])
                        if den == 0:
                            return None
                        return (num / den) + Decimal("1")
                    except InvalidOperation:
                        return None
            # americano +150 / -120
            if s.startswith(("+", "-")):
                try:
                    american = Decimal(s)
                    if american > 0:
                        return (american / Decimal("100")) + Decimal("1")
                    return (Decimal("100") / abs(american)) + Decimal("1")
                except InvalidOperation:
                    return None
            try:
                dec = Decimal(s)
                return dec if dec > 1 else None
            except InvalidOperation:
                return None
        return None
