from __future__ import annotations

from src.arbitrage.surebet_engine import detect_surebet
from src.models.schemas import CanonicalOdd, RevalidationResult, SurebetResult


def revalidate_with_new_snapshot(initial_result: SurebetResult, latest_legs: list[CanonicalOdd]) -> RevalidationResult:
    if not latest_legs:
        return RevalidationResult(False, 'expired', 'missing_latest_market', None)
    latest_result = detect_surebet(latest_legs, initial_result.event_key)
    if latest_result.reason == 'incomplete_market':
        return RevalidationResult(False, 'expired', 'incomplete_market', latest_result)
    if latest_result.implied_probability_sum >= 1 and latest_result.reason == 'no_longer_surebet':
        return RevalidationResult(False, 'expired', 'margin_lost', latest_result)
    if not latest_result.is_surebet:
        return RevalidationResult(False, 'expired', 'no_longer_surebet', latest_result)
    return RevalidationResult(True, 'validated', 'ok', latest_result)
