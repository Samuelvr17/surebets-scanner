"""Modelos de datos canónicos del scanner de surebets.

Separación en tres capas persistidas:
1) Captura cruda por casa (black box/auditoría).
2) Cuota normalizada (comparación cross-book).
3) Surebet detectada (resultado del motor de arbitraje).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional



def utc_now() -> datetime:
    """Devuelve fecha/hora aware en UTC."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RawOddsCapture:
    """Payload original recibido desde una casa de apuestas.

    `payload_json` se guarda tal cual (string JSON), sin transformar.
    `payload_hash` permite deduplicar contenido repetido.
    """

    id: Optional[int]
    bookmaker: str
    source_event_id: str
    fetched_at_utc: datetime
    payload_json: str
    payload_hash: str
    collector_version: str
    created_at_utc: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class NormalizedOdds:
    """Cuota estandarizada para comparación entre casas."""

    id: Optional[int]
    capture_id: int
    bookmaker: str
    canonical_event_key: str
    sport: str
    league: str
    home_team: str
    away_team: str
    event_start_utc: datetime
    market_type: str
    selection: str
    line_value: Optional[str]
    odds_decimal: Decimal
    normalized_at_utc: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class SurebetOpportunity:
    """Registro histórico de oportunidad de arbitraje detectada."""

    id: Optional[int]
    opportunity_key: str
    canonical_event_key: str
    market_type: str
    implied_probability_sum: Decimal
    expected_roi_percent: Decimal
    stake_plan_json: str
    legs_json: str
    detected_at_utc: datetime
    status: str  # detected | validated | expired | executed | rejected
    validated_at_utc: Optional[datetime] = None
    expires_at_utc: Optional[datetime] = None
    notes: Optional[str] = None
