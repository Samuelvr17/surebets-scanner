from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal


SourceType = Literal['local_snapshot', 'authorized_api', 'bookmaker_adapter']


@dataclass(slots=True, frozen=True)
class RawOddsRow:
    source_id: str
    payload: dict[str, Any]
    pulled_at_utc: datetime


@dataclass(slots=True, frozen=True)
class CanonicalOdd:
    bookmaker: str
    sport: str
    league: str
    home_team: str
    away_team: str
    event_start_utc: datetime
    market_family: str
    period: str
    side_code: str
    line_value: str | None
    line_unit: str | None
    selection: str
    odds_decimal: Decimal
    pulled_at_utc: datetime


@dataclass(slots=True, frozen=True)
class SourceHealth:
    source_id: str
    source_type: SourceType
    ok: bool
    detail: str


@dataclass(slots=True, frozen=True)
class SourceConfig:
    id: str
    type: SourceType
    enabled: bool
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class SurebetResult:
    is_surebet: bool
    event_key: str
    market_family: str
    period: str
    line_value: str | None
    line_unit: str | None
    implied_probability_sum: Decimal
    roi_percent: Decimal
    selected_legs: list[CanonicalOdd]
    reason: str
    stake_plan: dict[str, Decimal] | None = None


@dataclass(slots=True, frozen=True)
class RevalidationResult:
    is_valid: bool
    status: str
    reason: str
    latest_result: SurebetResult | None
