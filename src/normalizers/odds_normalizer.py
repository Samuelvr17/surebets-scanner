from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from src.models.schemas import CanonicalOdd

REQUIRED = [
    'bookmaker','sport','league','home_team','away_team','event_start_utc',
    'market_family','period','side_code','line_value','line_unit','selection','odds_decimal','pulled_at_utc'
]


def normalize_snapshots(rows: list[dict]) -> list[CanonicalOdd]:
    out: list[CanonicalOdd] = []
    for row in rows:
        for key in REQUIRED:
            if key not in row:
                raise ValueError(f'missing required field: {key}')
        out.append(
            CanonicalOdd(
                bookmaker=str(row['bookmaker']),
                sport=str(row['sport']),
                league=str(row['league']),
                home_team=str(row['home_team']),
                away_team=str(row['away_team']),
                event_start_utc=datetime.fromisoformat(row['event_start_utc'].replace('Z', '+00:00')).astimezone(UTC),
                market_family=str(row['market_family']),
                period=str(row['period']),
                side_code=str(row['side_code']).lower(),
                line_value=None if row['line_value'] is None else str(row['line_value']),
                line_unit=None if row['line_unit'] is None else str(row['line_unit']),
                selection=str(row['selection']),
                odds_decimal=Decimal(str(row['odds_decimal'])),
                pulled_at_utc=datetime.fromisoformat(row['pulled_at_utc'].replace('Z', '+00:00')).astimezone(UTC),
            )
        )
    return out
