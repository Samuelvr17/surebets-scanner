from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import timedelta

from src.models.schemas import CanonicalOdd


def _canon(name: str) -> str:
    value = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()
    value = re.sub(r'[^a-z0-9\s]', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def _event_key(odd: CanonicalOdd) -> str:
    return f"{odd.sport}|{_canon(odd.league)}|{_canon(odd.home_team)}|{_canon(odd.away_team)}|{odd.event_start_utc.isoformat()}"


def match_events(rows: list[CanonicalOdd], time_window_minutes: int = 5) -> dict[str, list[CanonicalOdd]]:
    grouped: dict[str, list[CanonicalOdd]] = defaultdict(list)
    canonical_events: list[tuple[CanonicalOdd, str]] = []
    for odd in rows:
        matched_key = None
        for base, key in canonical_events:
            if odd.sport != base.sport:
                continue
            if _canon(odd.league) != _canon(base.league):
                continue
            if abs(odd.event_start_utc - base.event_start_utc) > timedelta(minutes=time_window_minutes):
                continue
            same_orientation = _canon(odd.home_team) == _canon(base.home_team) and _canon(odd.away_team) == _canon(base.away_team)
            swapped = _canon(odd.home_team) == _canon(base.away_team) and _canon(odd.away_team) == _canon(base.home_team)
            if swapped:
                matched_key = None
                break
            if same_orientation:
                matched_key = key
                break
        if matched_key is None:
            matched_key = _event_key(odd)
            canonical_events.append((odd, matched_key))
        grouped[matched_key].append(odd)
    return grouped
