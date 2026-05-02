from decimal import Decimal

from src.arbitrage.surebet_engine import SurebetEngine, SurebetLeg


def test_two_way_market_returns_profitable_plan_with_conservative_rounding() -> None:
    engine = SurebetEngine(
        min_profit_percent=Decimal("1.00"),
        odds_safety_margin_percent=Decimal("0.00"),
        stake_increment=Decimal("100"),
    )
    legs = [
        SurebetLeg(bookmaker="betplay", selection="1", odds_decimal=Decimal("2.10")),
        SurebetLeg(bookmaker="rushbet", selection="2", odds_decimal=Decimal("2.05")),
    ]

    result = engine.evaluate(legs, total_budget=Decimal("100000"))

    assert result.is_surebet is True
    assert result.passes_threshold is True
    assert result.implied_probability_sum < Decimal("1")
    assert result.total_stake == Decimal("99900")
    assert result.guaranteed_profit == Decimal("3630.0000")
    assert result.guaranteed_profit_percent > Decimal("0")
    assert all((leg.stake % Decimal("100")) == 0 for leg in result.stake_plan)
    assert len(result.warning_messages) == 3


def test_three_way_market_is_rejected_if_profit_after_friction_is_too_small() -> None:
    engine = SurebetEngine(
        min_profit_percent=Decimal("7.00"),
        odds_safety_margin_percent=Decimal("0.40"),
        stake_increment=Decimal("100"),
    )
    legs = [
        SurebetLeg(bookmaker="betplay", selection="local", odds_decimal=Decimal("4.20")),
        SurebetLeg(bookmaker="codere", selection="empate", odds_decimal=Decimal("3.80")),
        SurebetLeg(bookmaker="stake", selection="visitante", odds_decimal=Decimal("2.30")),
    ]

    result = engine.evaluate(legs, total_budget=Decimal("150000"))

    assert result.is_surebet is True
    assert result.guaranteed_profit > Decimal("0")
    assert result.passes_threshold is False
    assert result.guaranteed_profit_percent < Decimal("7.00")
    assert len(result.stake_plan) == 3


def test_non_surebet_market_does_not_emit_plan() -> None:
    engine = SurebetEngine()
    legs = [
        SurebetLeg(bookmaker="betplay", selection="1", odds_decimal=Decimal("1.80")),
        SurebetLeg(bookmaker="rushbet", selection="2", odds_decimal=Decimal("1.95")),
    ]

    result = engine.evaluate(legs, total_budget=Decimal("100000"))

    assert result.is_surebet is False
    assert result.passes_threshold is False
    assert result.stake_plan == tuple()
    assert result.guaranteed_profit == Decimal("0")
