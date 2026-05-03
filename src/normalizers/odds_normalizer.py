from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from src.models.schemas import CanonicalOdd

REQUIRED = [
    'bookmaker','sport','league','home_team','away_team','event_start_utc',
    'market_family','period','side_code','line_value','line_unit','selection','odds_decimal','pulled_at_utc'
]
ALLOWED_SIDES = {
    '1x2': {'home', 'draw', 'away'},
    'moneyline_2way': {'home', 'away'},
    'totals': {'over', 'under'},
    'handicap': {'home', 'away'},
}

def _parse_dt(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(UTC)
    except ValueError as exc:
        raise ValueError(f"invalid datetime in {field}: '{value}' (expected ISO-8601)") from exc

def normalize_snapshots(rows: list[dict]) -> list[CanonicalOdd]:
    out: list[CanonicalOdd] = []
    for row in rows:
        for key in REQUIRED:
            if key not in row:
                raise ValueError(f'missing required field: {key}')
        market_family = str(row['market_family']).strip().lower()
        period = str(row['period']).strip().lower()
        side_code = str(row['side_code']).strip().lower()
        odds = Decimal(str(row['odds_decimal']))
        if odds <= Decimal('1'):
            raise ValueError(f'odds_decimal must be > 1, got {odds}')
        if market_family in ALLOWED_SIDES and side_code not in ALLOWED_SIDES[market_family]:
            raise ValueError(f"invalid side_code '{side_code}' for market_family '{market_family}'")
        out.append(CanonicalOdd(
            bookmaker=str(row['bookmaker']).strip().lower(),
            sport=str(row['sport']).strip().lower(),
            league=str(row['league']).strip(),
            home_team=str(row['home_team']).strip(),
            away_team=str(row['away_team']).strip(),
            event_start_utc=_parse_dt(str(row['event_start_utc']), 'event_start_utc'),
            market_family=market_family,
            period=period,
            side_code=side_code,
            line_value=None if row['line_value'] is None else str(row['line_value']).strip(),
            line_unit=None if row['line_unit'] is None else str(row['line_unit']).strip().lower(),
            selection=str(row['selection']).strip(),
            odds_decimal=odds,
            pulled_at_utc=_parse_dt(str(row['pulled_at_utc']), 'pulled_at_utc'),
        ))
    return out
