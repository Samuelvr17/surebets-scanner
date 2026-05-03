from __future__ import annotations

from decimal import Decimal

from src.models.schemas import CanonicalOdd, SurebetResult

REQUIRED = {'1x2': {'home', 'draw', 'away'}, 'moneyline_2way': {'home', 'away'}, 'totals': {'over', 'under'}}


def detect_surebet(legs: list[CanonicalOdd], event_key: str, bankroll: Decimal | None = None) -> SurebetResult:
    if not legs:
        return SurebetResult(False, event_key, '', '', None, None, Decimal('0'), Decimal('0'), [], 'empty_market')
    family = legs[0].market_family
    best: dict[str, CanonicalOdd] = {}
    for leg in legs:
        if leg.side_code not in REQUIRED.get(family, set()):
            continue
        if family == 'totals' and leg.line_value != legs[0].line_value:
            continue
        if leg.side_code not in best or leg.odds_decimal > best[leg.side_code].odds_decimal:
            best[leg.side_code] = leg
    selected = list(best.values())
    needed = REQUIRED.get(family, set())
    if needed and not needed.issubset(best.keys()):
        return SurebetResult(False, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, Decimal('0'), Decimal('0'), selected, 'incomplete_market')
    if len({x.bookmaker for x in selected}) < 2:
        return SurebetResult(False, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, Decimal('0'), Decimal('0'), selected, 'single_bookmaker')
    implied = sum(Decimal('1') / x.odds_decimal for x in selected)
    roi = ((Decimal('1') / implied) - Decimal('1')) * Decimal('100')
    is_sb = implied < Decimal('1')
    stake_plan = None
    if is_sb and bankroll:
        stake_plan = {f'{x.bookmaker}:{x.side_code}': (bankroll / (x.odds_decimal * implied)).quantize(Decimal('0.01')) for x in selected}
    return SurebetResult(is_sb, event_key, family, legs[0].period, legs[0].line_value, legs[0].line_unit, implied, roi, selected, 'ok' if is_sb else 'no_longer_surebet', stake_plan)
