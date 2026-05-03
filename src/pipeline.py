from __future__ import annotations

from pathlib import Path

from src.arbitrage.revalidation import revalidate_with_new_snapshot
from src.arbitrage.surebet_engine import detect_surebet
from src.collectors.base import LocalSnapshotCollector
from src.matchers.event_matcher import match_events
from src.normalizers.odds_normalizer import normalize_snapshots


def run_console_pipeline(input_dir: Path, initial_dataset: str, latest_dataset: str) -> list[str]:
    collector = LocalSnapshotCollector(input_dir)
    initial = normalize_snapshots(collector.collect(initial_dataset).snapshots)
    latest = normalize_snapshots(collector.collect(latest_dataset).snapshots)

    grouped_initial = match_events(initial)
    grouped_latest = match_events(latest)
    output: list[str] = []

    for key, legs in grouped_initial.items():
        if not detect_surebet(legs):
            continue
        latest_legs = grouped_latest.get(key, [])
        if revalidate_with_new_snapshot(legs, latest_legs):
            output.append(f"SUREBET VALIDADA: {key} ({legs[0].market_family})")
    return output
