from __future__ import annotations

from decimal import Decimal

from src.models.schemas import CanonicalOdd, SurebetResult


def _group_key(odd: CanonicalOdd) -> tuple[str, str, str, str | None, str | None]:
    if odd.market_family in {'totals', 'handicap'}:
        return (odd.event_key, odd.market_family, odd.period, odd.line_value, odd.line_unit)
    return (odd.event_key, odd.market_family, odd.period, None, None)


def detect_surebet(legs: list[CanonicalOdd], event_key: str) -> SurebetResult:
    if not legs:
        return SurebetResult(False, event_key, '', '', None, None, Decimal('0'), Decimal('0'), [], 'empty_market')
    best: dict[str, CanonicalOdd] = {}
    for leg in legs:
        current = best.get(leg.side_code)
        if current is None or leg.odds_decimal > current.odds_decimal:
            best[leg.side_code] = leg
    selected = list(best.values())
    family = legs[0].market_family
    required = {'1x2': {'home', 'draw', 'away'}, 'moneyline_2way': {'home', 'away'}, 'totals': {'over', 'under'}, 'handicap': {'home', 'away'}}.get(family, set())
    if required and not required.issubset({x.side_code for x in selected}):
        return SurebetResult(False, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, Decimal('0'), Decimal('0'), selected, 'incomplete_market')
    if family in {'totals', 'handicap'} and len({(x.line_value, x.line_unit) for x in selected}) > 1:
        return SurebetResult(False, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, Decimal('0'), Decimal('0'), selected, 'incomplete_market')
    if len({x.bookmaker for x in selected}) < 2:
        return SurebetResult(False, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, Decimal('0'), Decimal('0'), selected, 'single_bookmaker')
    implied = sum(Decimal('1') / x.odds_decimal for x in selected)
    roi = ((Decimal('1') / implied) - Decimal('1')) * Decimal('100')
    is_sb = implied < Decimal('1')
    return SurebetResult(is_sb, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, implied, roi, selected, 'ok' if is_sb else 'no_longer_surebet')
