from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import timedelta

import json

from src.models.schemas import CanonicalOdd


def _canon(name: str) -> str:
    value = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()
    value = re.sub(r'[^a-z0-9\s]', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def _alias_map(path: str | None) -> tuple[dict[str, str], dict[str, str]]:
    if not path:
        return {}, {}
    data = json.load(open(path, 'r', encoding='utf-8'))
    team_aliases = {_canon(k): _canon(v) for k, v in data.get('teams', {}).items()}
    league_aliases = {_canon(k): _canon(v) for k, v in data.get('leagues', {}).items()}
    return team_aliases, league_aliases


def _event_key(odd: CanonicalOdd, team_aliases: dict[str, str], league_aliases: dict[str, str]) -> str:
    league = league_aliases.get(_canon(odd.league), _canon(odd.league))
    home = team_aliases.get(_canon(odd.home_team), _canon(odd.home_team))
    away = team_aliases.get(_canon(odd.away_team), _canon(odd.away_team))
    return f"{odd.sport}|{league}|{home}|{away}|{odd.event_start_utc.isoformat()}"


def match_events(rows: list[CanonicalOdd], aliases_path: str | None = None, time_window_minutes: int = 0) -> dict[str, list[CanonicalOdd]]:
    grouped: dict[str, list[CanonicalOdd]] = defaultdict(list)
    team_aliases, league_aliases = _alias_map(aliases_path)
    canonical_events: list[tuple[CanonicalOdd, str]] = []
    for odd in rows:
        matched_key = None
        for base, key in canonical_events:
            if odd.sport != base.sport:
                continue
            ol = league_aliases.get(_canon(odd.league), _canon(odd.league))
            bl = league_aliases.get(_canon(base.league), _canon(base.league))
            if ol != bl:
                continue
            if abs(odd.event_start_utc - base.event_start_utc) > timedelta(minutes=time_window_minutes):
                continue
            oh = team_aliases.get(_canon(odd.home_team), _canon(odd.home_team))
            oa = team_aliases.get(_canon(odd.away_team), _canon(odd.away_team))
            bh = team_aliases.get(_canon(base.home_team), _canon(base.home_team))
            ba = team_aliases.get(_canon(base.away_team), _canon(base.away_team))
            if oh == ba and oa == bh:
                matched_key = None
                break
            if oh == bh and oa == ba:
                matched_key = key
                break
        if matched_key is None:
            matched_key = _event_key(odd, team_aliases, league_aliases)
            canonical_events.append((odd, matched_key))
        grouped[matched_key].append(odd)
    return grouped
