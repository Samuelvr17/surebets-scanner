"""Revalidación operativa de surebets antes de alertar al usuario."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable

from src.arbitrage.surebet_engine import SurebetEngine, SurebetLeg
from src.models.schemas import SurebetOpportunity, utc_now
from src.storage.repositories import SurebetRepository


@dataclass(frozen=True, slots=True)
class RevalidationConfig:
    """Parámetros operativos de la revalidación."""

    delay_seconds: float = 1.2
    max_odds_drop_percent: Decimal = Decimal("1.00")


@dataclass(frozen=True, slots=True)
class RevalidationMetrics:
    """Contadores de calidad para monitorear latencia/frescura."""

    revalidation_attempts: int = 0
    revalidation_validated: int = 0
    revalidation_expired: int = 0


@dataclass(frozen=True, slots=True)
class RevalidationResult:
    is_valid: bool
    status: str
    reason: str
    refreshed_legs: tuple[SurebetLeg, ...]


OddsSnapshotFetcher = Callable[[str, str, str], tuple[Decimal, bool]]


class SurebetRevalidator:
    """Reconsulta cuotas/mercados y confirma si la oportunidad sigue viva."""

    def __init__(self, engine: SurebetEngine, config: RevalidationConfig | None = None) -> None:
        self.engine = engine
        self.config = config or RevalidationConfig()
        self.metrics = RevalidationMetrics()

    def revalidate(
        self,
        *,
        opportunity: SurebetOpportunity,
        fetch_current_leg: OddsSnapshotFetcher,
        total_budget: Decimal,
    ) -> RevalidationResult:
        self._bump_metric("revalidation_attempts")
        time.sleep(self.config.delay_seconds)

        original_legs = tuple(self._parse_legs(opportunity.legs_json))
        refreshed_legs: list[SurebetLeg] = []

        for leg in original_legs:
            current_odds, is_market_open = fetch_current_leg(
                leg.bookmaker,
                opportunity.canonical_event_key,
                leg.selection,
            )
            if not is_market_open:
                self._expire(opportunity, "market_closed")
                return RevalidationResult(False, "expired", "market_closed", tuple())
            if self._dropped_too_much(leg.odds_decimal, current_odds):
                self._expire(opportunity, "odds_changed")
                return RevalidationResult(False, "expired", "odds_changed", tuple())
            refreshed_legs.append(
                SurebetLeg(
                    bookmaker=leg.bookmaker,
                    selection=leg.selection,
                    odds_decimal=current_odds,
                )
            )

        evaluation = self.engine.evaluate(refreshed_legs, total_budget=total_budget)
        if not evaluation.is_surebet or not evaluation.passes_threshold:
            self._expire(opportunity, "margin_lost")
            return RevalidationResult(False, "expired", "margin_lost", tuple(refreshed_legs))

        self._bump_metric("revalidation_validated")
        return RevalidationResult(True, "validated", "ok", tuple(refreshed_legs))

    def apply_result(self, repo: SurebetRepository, opportunity_key: str, result: RevalidationResult) -> None:
        repo.mark_status(opportunity_key, result.status)

    def expiration_ratio(self) -> Decimal:
        if self.metrics.revalidation_attempts == 0:
            return Decimal("0")
        return Decimal(self.metrics.revalidation_expired) / Decimal(self.metrics.revalidation_attempts)

    def _expire(self, opportunity: SurebetOpportunity, reason: str) -> None:
        self._bump_metric("revalidation_expired")
        opportunity.status = "expired"
        opportunity.expires_at_utc = utc_now()
        opportunity.notes = f"revalidation:{reason}"

    def _bump_metric(self, field_name: str) -> None:
        current = getattr(self.metrics, field_name)
        object.__setattr__(self.metrics, field_name, current + 1)

    def _dropped_too_much(self, previous: Decimal, current: Decimal) -> bool:
        if current >= previous:
            return False
        drop_pct = ((previous - current) / previous) * Decimal("100")
        return drop_pct > self.config.max_odds_drop_percent

    @staticmethod
    def _parse_legs(legs_json: str) -> list[SurebetLeg]:
        payload = json.loads(legs_json)
        return [
            SurebetLeg(
                bookmaker=leg["bookmaker"],
                selection=leg["selection"],
                odds_decimal=Decimal(str(leg["odds_decimal"])),
            )
            for leg in payload
        ]
