from __future__ import annotations

from src.models.schemas import CanonicalOdd
from src.arbitrage.surebet_engine import detect_surebet


def revalidate_with_new_snapshot(initial_legs: list[CanonicalOdd], latest_legs: list[CanonicalOdd]) -> bool:
    # must use newest snapshot only
    return detect_surebet(latest_legs)
