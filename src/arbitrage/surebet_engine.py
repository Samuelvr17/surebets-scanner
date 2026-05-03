from __future__ import annotations

from decimal import Decimal

from src.models.schemas import CanonicalOdd


def _is_complete_market(legs: list[CanonicalOdd]) -> bool:
    family = legs[0].market_family
    sides = {x.side_code for x in legs}
    if family == '1x2':
        return {'home','draw','away'}.issubset(sides)
    if family == 'totals':
        if not {'over','under'}.issubset(sides):
            return False
        lines = {(x.line_value, x.line_unit) for x in legs if x.side_code in {'over','under'}}
        return len(lines) == 1
    if family == 'moneyline_2way':
        return {'home','away'}.issubset(sides)
    return False


def detect_surebet(legs: list[CanonicalOdd]) -> bool:
    best: dict[str, CanonicalOdd] = {}
    for leg in legs:
        if leg.side_code not in best or leg.odds_decimal > best[leg.side_code].odds_decimal:
            best[leg.side_code] = leg
    selected = list(best.values())
    if not selected or not _is_complete_market(selected):
        return False
    implied = sum(Decimal('1') / x.odds_decimal for x in selected)
    return implied < Decimal('1')
