"""Pipeline E2E desde capturas crudas hasta surebets revalidadas."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.arbitrage.revalidation import RevalidationConfig, SurebetRevalidator
from src.arbitrage.surebet_engine import SurebetEngine, SurebetLeg
from src.config.settings import AppConfig
from src.matchers.event_matcher import EventMatcher, EventOddsSnapshot
from src.models.schemas import SurebetOpportunity, utc_now
from src.normalizers.odds_normalizer import NormalizedOddRecord, OddsNormalizer
from src.storage.database import get_connection, init_db
from src.storage.repositories import SurebetRepository


@dataclass(slots=True)
class RevalidatedOpportunityView:
    opportunity: SurebetOpportunity
    stake_plan: tuple[Any, ...]


def _load_raw_files(raw_dump_dir: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    if not raw_dump_dir.exists():
        return payloads
    for bookmaker_dir in raw_dump_dir.iterdir():
        if not bookmaker_dir.is_dir():
            continue
        for raw_file in sorted(bookmaker_dir.glob("*.json")):
            try:
                payloads.append(json.loads(raw_file.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
    return payloads


def _extract_event_payloads(bookmaker: str, capture_payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    candidates: list[tuple[str, dict[str, Any]]] = []

    if {"home_team", "away_team", "league", "event_start", "odds"}.issubset(capture_payload.keys()):
        source_id = str(capture_payload.get("event_id", "unknown-event"))
        return [(source_id, capture_payload)]

    raw = capture_payload.get("raw_json")
    if isinstance(raw, list):
        iterable = raw
    elif isinstance(raw, dict):
        for key in ("events", "fixtures", "matches", "data"):
            value = raw.get(key)
            if isinstance(value, list):
                iterable = value
                break
        else:
            iterable = [raw]
    else:
        iterable = []

    for idx, item in enumerate(iterable):
        if not isinstance(item, dict):
            continue
        normalized_shape = {
            "home_team": item.get("home_team") or item.get("home") or item.get("team_home"),
            "away_team": item.get("away_team") or item.get("away") or item.get("team_away"),
            "league": item.get("league") or item.get("competition") or item.get("tournament"),
            "event_start": item.get("event_start") or item.get("start_time") or item.get("kickoff"),
            "odds": item.get("odds") or item.get("markets") or [],
        }
        if not isinstance(normalized_shape["odds"], list):
            continue
        if not normalized_shape["home_team"] or not normalized_shape["away_team"]:
            continue
        source_id = str(item.get("event_id") or item.get("id") or f"{bookmaker}-evt-{idx}")
        candidates.append((source_id, normalized_shape))

    return candidates


def run_full_processing_pipeline(config: AppConfig, total_budget: Decimal = Decimal("100000")) -> list[RevalidatedOpportunityView]:
    init_db()
    conn = get_connection()
    surebet_repo = SurebetRepository(conn)

    normalizer = OddsNormalizer()
    matcher = EventMatcher(max_start_diff_minutes=5)
    engine = SurebetEngine()
    revalidator = SurebetRevalidator(engine=engine, config=RevalidationConfig(delay_seconds=0))

    raw_payloads = _load_raw_files(config.runtime.raw_dump_dir)

    normalized_records: list[NormalizedOddRecord] = []
    for payload in raw_payloads:
        bookmaker = str(payload.get("bookmaker", "")).strip().lower().replace(" ", "_")
        source_id = str(payload.get("event_id", "unknown-event"))

        for extracted_source_id, event_payload in _extract_event_payloads(bookmaker, payload):
            result = normalizer.normalize_payload(bookmaker, extracted_source_id or source_id, event_payload)
            normalized_records.extend(result.normalized)

    snapshots: list[EventOddsSnapshot] = [
        EventOddsSnapshot(
            bookmaker=r.bookmaker,
            source_event_id=r.source_event_id,
            sport="futbol",
            league=r.league,
            home_team=r.home_team,
            away_team=r.away_team,
            event_start_utc=r.event_start_utc,
            market_type=r.market_type,
            selection=r.selection,
            line_value=r.line_value,
            odds_decimal=r.odds_decimal,
        )
        for r in normalized_records
    ]

    grouped_by_signature: dict[tuple[str, str, str, str, str], list[EventOddsSnapshot]] = defaultdict(list)
    for snap in snapshots:
        key = (
            snap.market_type,
            snap.league,
            snap.home_team,
            snap.away_team,
            snap.event_start_utc.isoformat(),
        )
        grouped_by_signature[key].append(snap)

    opportunities: list[RevalidatedOpportunityView] = []
    for group in grouped_by_signature.values():
        if len(group) < 2:
            continue

        match_result = matcher.match(group)
        if not match_result.auto_matched:
            continue

        by_selection_best: dict[str, EventOddsSnapshot] = {}
        for row in group:
            current = by_selection_best.get(row.selection)
            if current is None or row.odds_decimal > current.odds_decimal:
                by_selection_best[row.selection] = row

        if len(by_selection_best) < 2:
            continue

        legs = [
            SurebetLeg(bookmaker=v.bookmaker, selection=v.selection, odds_decimal=v.odds_decimal)
            for v in by_selection_best.values()
        ]
        evaluation = engine.evaluate(legs, total_budget=total_budget)
        if not evaluation.is_surebet or not evaluation.passes_threshold:
            continue

        opportunity_key = "|".join([
            group[0].league,
            group[0].home_team,
            group[0].away_team,
            group[0].event_start_utc.isoformat(),
            group[0].market_type,
        ])

        surebet = SurebetOpportunity(
            id=None,
            opportunity_key=opportunity_key,
            canonical_event_key=opportunity_key,
            market_type=group[0].market_type,
            implied_probability_sum=evaluation.implied_probability_sum,
            expected_roi_percent=evaluation.guaranteed_profit_percent,
            stake_plan_json=json.dumps([
                {
                    "bookmaker": s.bookmaker,
                    "selection": s.selection,
                    "odds_decimal": str(s.odds_decimal),
                    "stake": str(s.stake),
                }
                for s in evaluation.stake_plan
            ], ensure_ascii=False),
            legs_json=json.dumps([
                {"bookmaker": leg.bookmaker, "selection": leg.selection, "odds_decimal": str(leg.odds_decimal)}
                for leg in legs
            ], ensure_ascii=False),
            detected_at_utc=utc_now(),
            status="detected",
        )

        surebet_repo.insert_or_ignore(surebet)

        leg_map = {(s.bookmaker, s.selection): s.odds_decimal for s in group}

        revalidation = revalidator.revalidate(
            opportunity=surebet,
            total_budget=total_budget,
            fetch_current_leg=lambda bookmaker, _event, selection: (
                leg_map.get((bookmaker, selection), Decimal("0")),
                (bookmaker, selection) in leg_map,
            ),
        )
        revalidator.apply_result(surebet_repo, surebet.opportunity_key, revalidation)
        if revalidation.is_valid:
            surebet.status = "validated"
            opportunities.append(RevalidatedOpportunityView(opportunity=surebet, stake_plan=evaluation.stake_plan))

    conn.close()
    return opportunities
