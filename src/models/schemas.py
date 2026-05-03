from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


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


@dataclass(slots=True)
class SurebetCandidate:
    event_key: str
    market_key: str
    market_family: str
    legs: list[CanonicalOdd]
