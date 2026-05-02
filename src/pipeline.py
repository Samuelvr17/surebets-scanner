"""Orquestador principal de captura cruda por colectores independientes."""

from __future__ import annotations

from importlib import import_module

from src.collectors.base import BaseBookmakerCollector, CollectorResult
from src.config.settings import AppConfig


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
