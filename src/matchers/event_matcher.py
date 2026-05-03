from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

from src.models.schemas import CanonicalOdd


def _canon(name: str) -> str:
    value = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()
    value = re.sub(r'[^a-z0-9\s]', ' ', value)
    value = re.sub(r'\b(fc|club|cf|deportivo|atletico|los)\b', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(a=_canon(a), b=_canon(b)).ratio()


def match_events(rows: list[CanonicalOdd], threshold: float = 0.84) -> dict[str, list[CanonicalOdd]]:
    groups: dict[str, list[CanonicalOdd]] = defaultdict(list)
    for odd in rows:
        matched_key = None
        for key, grouped in groups.items():
            base = grouped[0]
            team_score = (_sim(base.home_team, odd.home_team) + _sim(base.away_team, odd.away_team)) / 2
            swap_score = (_sim(base.home_team, odd.away_team) + _sim(base.away_team, odd.home_team)) / 2
            if max(team_score, swap_score) >= threshold and base.market_family == odd.market_family and base.period == odd.period:
                matched_key = key
                break
        if matched_key is None:
            matched_key = f"evt-{len(groups)+1}"
        groups[matched_key].append(odd)
    return groups
