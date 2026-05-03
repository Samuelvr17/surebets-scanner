from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from src.arbitrage.revalidation import revalidate_with_new_snapshot
from src.arbitrage.surebet_engine import detect_surebet
from src.collectors.base import LocalSnapshotCollector
from src.matchers.event_matcher import match_events
from src.models.schemas import CanonicalOdd
from src.normalizers.odds_normalizer import normalize_snapshots


def _market_group_key(event_key: str, odd: CanonicalOdd) -> tuple:
    if odd.market_family in {'totals', 'handicap'}:
        return (event_key, odd.market_family, odd.period, odd.line_value, odd.line_unit)
    return (event_key, odd.market_family, odd.period)


def run_console_pipeline(input_dir: Path, initial_dataset: str, latest_dataset: str) -> list[str]:
    collector = LocalSnapshotCollector(input_dir)
    initial = normalize_snapshots(collector.collect(initial_dataset).snapshots)
    latest = normalize_snapshots(collector.collect(latest_dataset).snapshots)

    grouped_initial = match_events(initial)
    grouped_latest = match_events(latest)
    output: list[str] = []

    for event_key, event_legs in grouped_initial.items():
        markets: dict[tuple, list[CanonicalOdd]] = defaultdict(list)
        for leg in event_legs:
            markets[_market_group_key(event_key, leg)].append(leg)

        for group_key, legs in markets.items():
            initial_result = detect_surebet(legs, event_key)
            if not initial_result.is_surebet:
                continue
            latest_event = grouped_latest.get(event_key, [])
            latest_market = [l for l in latest_event if _market_group_key(event_key, l) == group_key]
            revalidation = revalidate_with_new_snapshot(initial_result, latest_market)
            if not revalidation.is_valid:
                continue
            line_text = f" | línea: {initial_result.line_value} {initial_result.line_unit}" if initial_result.line_value else ""
            lines = [
                f"evento: {event_key}",
                f"mercado: {initial_result.market_family}",
                f"periodo: {initial_result.period}{line_text}",
                f"ROI: {initial_result.roi_percent:.2f}%",
                f"suma implícita: {initial_result.implied_probability_sum:.6f}",
            ]
            for leg in initial_result.selected_legs:
                lines.append(f"pata: {leg.bookmaker} | {leg.side_code} | {leg.selection} | {leg.odds_decimal}")
            lines.append(f"revalidación: {revalidation.status}")
            output.append('\n'.join(lines))
    return output
