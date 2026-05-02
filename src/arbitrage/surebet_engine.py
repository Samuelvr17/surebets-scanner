"""Motor de cálculo de surebets con fricciones operativas realistas."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN


@dataclass(frozen=True, slots=True)
class SurebetLeg:
    """Una pierna elegible de la surebet."""

    bookmaker: str
    selection: str
    odds_decimal: Decimal


@dataclass(frozen=True, slots=True)
class StakePlanLeg:
    """Resultado de stake recomendado por pierna."""

    bookmaker: str
    selection: str
    odds_decimal: Decimal
    stake: Decimal
    payout_if_wins: Decimal


@dataclass(frozen=True, slots=True)
class SurebetEvaluation:
    """Resultado final del motor con métricas y advertencias."""

    is_surebet: bool
    passes_threshold: bool
    implied_probability_sum: Decimal
    theoretical_roi_percent: Decimal
    guaranteed_profit: Decimal
    guaranteed_profit_percent: Decimal
    total_stake: Decimal
    min_payout: Decimal
    stake_plan: tuple[StakePlanLeg, ...]
    warning_messages: tuple[str, ...]


class SurebetEngine:
    """Evalúa oportunidades de arbitraje y genera staking conservador."""

    def __init__(
        self,
        *,
        min_profit_percent: Decimal = Decimal("1.20"),
        odds_safety_margin_percent: Decimal = Decimal("0.50"),
        stake_increment: Decimal = Decimal("100"),
    ) -> None:
        self.min_profit_percent = min_profit_percent
        self.odds_safety_margin_percent = odds_safety_margin_percent
        self.stake_increment = stake_increment

    def evaluate(self, legs: list[SurebetLeg], total_budget: Decimal) -> SurebetEvaluation:
        if len(legs) < 2:
            raise ValueError("Se requieren al menos dos resultados para evaluar arbitraje")
        if total_budget <= 0:
            raise ValueError("El presupuesto total debe ser positivo")

        adjusted_legs = [
            SurebetLeg(
                bookmaker=leg.bookmaker,
                selection=leg.selection,
                odds_decimal=self._apply_safety_margin(leg.odds_decimal),
            )
            for leg in legs
        ]

        implied_sum = sum(Decimal("1") / leg.odds_decimal for leg in adjusted_legs)
        theoretical_roi = (Decimal("1") / implied_sum - Decimal("1")) * Decimal("100")
        is_surebet = implied_sum < Decimal("1")

        if not is_surebet:
            return SurebetEvaluation(
                is_surebet=False,
                passes_threshold=False,
                implied_probability_sum=implied_sum,
                theoretical_roi_percent=theoretical_roi,
                guaranteed_profit=Decimal("0"),
                guaranteed_profit_percent=Decimal("0"),
                total_stake=Decimal("0"),
                min_payout=Decimal("0"),
                stake_plan=tuple(),
                warning_messages=self._standard_warnings(),
            )

        target_payout = total_budget / implied_sum
        stake_plan = []
        for leg in adjusted_legs:
            raw_stake = target_payout / leg.odds_decimal
            rounded_stake = self._round_down_to_increment(raw_stake, self.stake_increment)
            payout = rounded_stake * leg.odds_decimal
            stake_plan.append(
                StakePlanLeg(
                    bookmaker=leg.bookmaker,
                    selection=leg.selection,
                    odds_decimal=leg.odds_decimal,
                    stake=rounded_stake,
                    payout_if_wins=payout,
                )
            )

        total_staked = sum(leg.stake for leg in stake_plan)
        min_payout = min(leg.payout_if_wins for leg in stake_plan)
        guaranteed_profit = min_payout - total_staked
        guaranteed_profit_pct = (guaranteed_profit / total_staked) * Decimal("100") if total_staked else Decimal("0")

        passes_threshold = guaranteed_profit_pct >= self.min_profit_percent and guaranteed_profit > 0

        return SurebetEvaluation(
            is_surebet=True,
            passes_threshold=passes_threshold,
            implied_probability_sum=implied_sum,
            theoretical_roi_percent=theoretical_roi,
            guaranteed_profit=guaranteed_profit,
            guaranteed_profit_percent=guaranteed_profit_pct,
            total_stake=total_staked,
            min_payout=min_payout,
            stake_plan=tuple(stake_plan),
            warning_messages=self._standard_warnings(),
        )

    def _apply_safety_margin(self, odds: Decimal) -> Decimal:
        if odds <= Decimal("1"):
            raise ValueError("Toda cuota decimal debe ser mayor que 1")
        discount = Decimal("1") - (self.odds_safety_margin_percent / Decimal("100"))
        adjusted = (odds - Decimal("1")) * discount + Decimal("1")
        return adjusted.quantize(Decimal("0.0001"), rounding=ROUND_DOWN)

    @staticmethod
    def _round_down_to_increment(value: Decimal, increment: Decimal) -> Decimal:
        if increment <= 0:
            raise ValueError("El incremento de stake debe ser positivo")
        units = (value / increment).to_integral_value(rounding=ROUND_DOWN)
        return units * increment

    @staticmethod
    def _standard_warnings() -> tuple[str, ...]:
        return (
            "No se validan límites máximos/mínimos de apuesta por casa.",
            "No se conoce si la cuenta del usuario tiene restricciones internas.",
            "No se garantiza que la cuota siga disponible al momento de ejecutar.",
        )
