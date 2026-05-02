import json
from decimal import Decimal

from src.arbitrage.revalidation import RevalidationConfig, SurebetRevalidator
from src.arbitrage.surebet_engine import SurebetEngine
from src.models.schemas import SurebetOpportunity, utc_now


def _opportunity(odds_a: str = "2.10", odds_b: str = "2.05") -> SurebetOpportunity:
    return SurebetOpportunity(
        id=None,
        opportunity_key="opp-1",
        canonical_event_key="match-1",
        market_type="1X2",
        implied_probability_sum=Decimal("0.95"),
        expected_roi_percent=Decimal("2.10"),
        stake_plan_json="[]",
        legs_json=json.dumps(
            [
                {"bookmaker": "betplay", "selection": "1", "odds_decimal": odds_a},
                {"bookmaker": "rushbet", "selection": "2", "odds_decimal": odds_b},
            ]
        ),
        detected_at_utc=utc_now(),
        status="detected",
        validated_at_utc=None,
        expires_at_utc=None,
        notes=None,
    )


def test_revalidation_expires_when_market_closed() -> None:
    engine = SurebetEngine(min_profit_percent=Decimal("0.50"), odds_safety_margin_percent=Decimal("0"))
    revalidator = SurebetRevalidator(engine=engine, config=RevalidationConfig(delay_seconds=0))

    result = revalidator.revalidate(
        opportunity=_opportunity(),
        total_budget=Decimal("100000"),
        fetch_current_leg=lambda *_args: (Decimal("2.10"), False),
    )

    assert result.is_valid is False
    assert result.reason == "market_closed"
    assert revalidator.metrics.revalidation_expired == 1


def test_revalidation_validates_when_odds_remain_profitable() -> None:
    engine = SurebetEngine(min_profit_percent=Decimal("0.50"), odds_safety_margin_percent=Decimal("0"))
    revalidator = SurebetRevalidator(engine=engine, config=RevalidationConfig(delay_seconds=0))

    snapshots = {
        ("betplay", "1"): (Decimal("2.10"), True),
        ("rushbet", "2"): (Decimal("2.05"), True),
    }

    result = revalidator.revalidate(
        opportunity=_opportunity(),
        total_budget=Decimal("100000"),
        fetch_current_leg=lambda bookmaker, _event, selection: snapshots[(bookmaker, selection)],
    )

    assert result.is_valid is True
    assert result.status == "validated"
    assert revalidator.metrics.revalidation_validated == 1
    assert revalidator.expiration_ratio() == Decimal("0")
