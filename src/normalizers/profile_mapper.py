from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import json


def _get_path(data: Any, path: str) -> Any:
    cur = data
    for token in path.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(token)
        else:
            return None
    return cur


def map_profile_payload(raw_payload: dict, profile_path: str, source_id: str) -> tuple[list[dict], list[str]]:
    profile = json.load(open(profile_path, 'r', encoding='utf-8'))
    errors: list[str] = []
    out: list[dict] = []
    markets = _get_path(raw_payload, profile['markets_path']) or []
    for m_idx, market in enumerate(markets):
        selections = _get_path(market, profile['selection_path']) or []
        for s_idx, selection in enumerate(selections):
            try:
                out.append({
                    'bookmaker': source_id,
                    'sport': profile.get('sport', 'soccer'),
                    'league': _get_path(raw_payload, profile['league_path']),
                    'home_team': _get_path(raw_payload, profile['home_team_path']),
                    'away_team': _get_path(raw_payload, profile['away_team_path']),
                    'event_start_utc': _get_path(raw_payload, profile['start_time_path']),
                    'market_family': _get_path(market, profile['market_name_path']),
                    'period': profile.get('default_period', 'ft'),
                    'side_code': selection.get('side_code', selection.get('code')),
                    'line_value': selection.get(profile.get('line_path', 'line')),
                    'line_unit': profile.get('line_unit', 'goals'),
                    'selection': selection.get('name'),
                    'odds_decimal': selection.get(profile['odds_path']),
                    'pulled_at_utc': datetime.now(UTC).isoformat(),
                })
            except Exception as exc:  # noqa: BLE001
                errors.append(f'market {m_idx} selection {s_idx}: {exc}')
    if not out and not errors:
        errors.append('profile produced 0 rows')
    return out, errors
