from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

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

@dataclass(slots=True)
class NormalizationOutcome:
    rows: list[CanonicalOdd]
    errors: list[str]


def _parse_dt(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(UTC)
    except ValueError as exc:
        raise ValueError(f"invalid datetime in {field}: '{value}'") from exc


def _normalize_row(row: dict) -> CanonicalOdd:
    for key in REQUIRED:
        if key not in row:
            raise ValueError(f'missing required field: {key}')
    market_family = str(row['market_family']).strip().lower()
    if market_family not in ALLOWED_SIDES:
        raise ValueError(f"unknown market_family '{market_family}'")
    side_code = str(row['side_code']).strip().lower()
    if side_code not in ALLOWED_SIDES[market_family]:
        raise ValueError(f"invalid side_code '{side_code}' for market_family '{market_family}'")
    try:
        odds = Decimal(str(row['odds_decimal']))
    except InvalidOperation as exc:
        raise ValueError(f"invalid odds_decimal '{row['odds_decimal']}'") from exc
    if odds <= Decimal('1'):
        raise ValueError(f'odds_decimal must be > 1, got {odds}')
    return CanonicalOdd(
        bookmaker=str(row['bookmaker']).strip().lower(),
        sport=str(row['sport']).strip().lower(),
        league=str(row['league']).strip(),
        home_team=str(row['home_team']).strip(),
        away_team=str(row['away_team']).strip(),
        event_start_utc=_parse_dt(str(row['event_start_utc']), 'event_start_utc'),
        market_family=market_family,
        period=str(row['period']).strip().lower(),
        side_code=side_code,
        line_value=None if row['line_value'] is None else str(row['line_value']).strip(),
        line_unit=None if row['line_unit'] is None else str(row['line_unit']).strip().lower(),
        selection=str(row['selection']).strip(),
        odds_decimal=odds,
        pulled_at_utc=_parse_dt(str(row['pulled_at_utc']), 'pulled_at_utc'),
    )


def normalize_snapshots_with_errors(rows: list[dict]) -> NormalizationOutcome:
    ok, errors = [], []
    for idx, row in enumerate(rows):
        try:
            ok.append(_normalize_row(row))
        except ValueError as exc:
            errors.append(f'row[{idx}]: {exc}')
    return NormalizationOutcome(rows=ok, errors=errors)


def normalize_snapshots(rows: list[dict]) -> list[CanonicalOdd]:
    outcome = normalize_snapshots_with_errors(rows)
    if outcome.errors:
        raise ValueError('; '.join(outcome.errors))
    return outcome.rows
