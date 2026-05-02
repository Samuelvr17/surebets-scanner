"""Orquestador principal de captura cruda por colectores independientes."""

from __future__ import annotations

from importlib import import_module
from decimal import Decimal

from src.arbitrage.revalidation import OddsSnapshotFetcher, SurebetRevalidator
from src.collectors.base import BaseBookmakerCollector, CollectorResult
from src.config.settings import AppConfig
from src.models.schemas import SurebetOpportunity
from src.storage.repositories import SurebetRepository


def _resolve_collector_class(bookmaker: str) -> type[BaseBookmakerCollector]:
    module = import_module(f"src.collectors.{bookmaker}")
    return getattr(module, "Collector")


def run_capture_pipeline(config: AppConfig) -> list[CollectorResult]:
    results: list[CollectorResult] = []
    for bookmaker, bookmaker_cfg in config.bookmakers.items():
        if not bookmaker_cfg.enabled:
            continue
        collector_cls = _resolve_collector_class(bookmaker)
        collector = collector_cls(runtime=config.runtime, bookmaker_config=bookmaker_cfg)
        results.append(collector.collect())
    return results


def revalidate_before_alert(
    *,
    opportunity: SurebetOpportunity,
    revalidator: SurebetRevalidator,
    repository: SurebetRepository,
    fetch_current_leg: OddsSnapshotFetcher,
    total_budget: Decimal,
) -> bool:
    """Puerta entre detección y alerta: valida o expira silenciosamente."""
    result = revalidator.revalidate(
        opportunity=opportunity,
        fetch_current_leg=fetch_current_leg,
        total_budget=total_budget,
    )
    revalidator.apply_result(repository, opportunity.opportunity_key, result)
    return result.is_valid
