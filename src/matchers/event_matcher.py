"""Motor de matching de eventos entre casas con niveles de confianza.

Reglas:
- Solo se considera match si deporte y liga son compatibles.
- Equipos deben coincidir en cualquier orden (local/visitante invertido permitido).
- Hora de inicio con tolerancia configurable en minutos.
- Matches de baja confianza se envían a revisión manual y nunca a arbitraje.
- Detecta patrones de feed compartido cuando dos casas repiten cuotas idénticas.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from difflib import SequenceMatcher


@dataclass(slots=True)
class EventOddsSnapshot:
    bookmaker: str
    source_event_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    event_start_utc: datetime
    market_type: str
    selection: str
    line_value: str | None
    odds_decimal: Decimal


@dataclass(slots=True)
class MatchCandidate:
    left_event_id: str
    right_event_id: str
    left_bookmaker: str
    right_bookmaker: str
    confidence: str  # high | low
    score: float
    reasons: list[str]


@dataclass(slots=True)
class MatchResult:
    auto_matched: list[MatchCandidate]
    manual_review: list[MatchCandidate]
    shared_feed_warnings: list[str]


class EventMatcher:
    def __init__(
        self,
        max_start_diff_minutes: int = 5,
        high_similarity_threshold: float = 0.98,
        low_similarity_threshold: float = 0.88,
    ) -> None:
        self.max_start_diff = timedelta(minutes=max_start_diff_minutes)
        self.high_similarity_threshold = high_similarity_threshold
        self.low_similarity_threshold = low_similarity_threshold

    def match(self, events: list[EventOddsSnapshot]) -> MatchResult:
        auto_matched: list[MatchCandidate] = []
        manual_review: list[MatchCandidate] = []

        for i, left in enumerate(events):
            for right in events[i + 1 :]:
                if left.bookmaker == right.bookmaker:
                    continue
                candidate = self._build_candidate(left, right)
                if not candidate:
                    continue
                if candidate.confidence == "high":
                    auto_matched.append(candidate)
                else:
                    manual_review.append(candidate)

        warnings = self._detect_shared_feed(events, auto_matched)
        return MatchResult(auto_matched=auto_matched, manual_review=manual_review, shared_feed_warnings=warnings)

    def _build_candidate(self, left: EventOddsSnapshot, right: EventOddsSnapshot) -> MatchCandidate | None:
        reasons: list[str] = []

        sport_similarity = self._similarity(left.sport, right.sport)
        if sport_similarity < self.low_similarity_threshold:
            return None

        league_similarity = self._similarity(left.league, right.league)
        if league_similarity < self.low_similarity_threshold:
            return None

        team_similarity = self._teams_similarity(left, right)
        if team_similarity < self.low_similarity_threshold:
            return None

        time_diff = abs(left.event_start_utc - right.event_start_utc)
        if time_diff > self.max_start_diff:
            return None

        if sport_similarity >= self.high_similarity_threshold:
            reasons.append("sport_exact_or_near_exact")
        else:
            reasons.append("sport_similar")

        if league_similarity >= self.high_similarity_threshold:
            reasons.append("league_exact_or_near_exact")
        else:
            reasons.append("league_similar")

        if team_similarity >= self.high_similarity_threshold:
            reasons.append("teams_exact_or_near_exact")
        else:
            reasons.append("teams_similar_needs_review")

        reasons.append(f"kickoff_within_{int(self.max_start_diff.total_seconds() // 60)}m")

        min_similarity = min(sport_similarity, league_similarity, team_similarity)
        if (
            sport_similarity >= self.high_similarity_threshold
            and league_similarity >= self.high_similarity_threshold
            and team_similarity >= self.high_similarity_threshold
        ):
            confidence = "high"
        else:
            confidence = "low"

        return MatchCandidate(
            left_event_id=left.source_event_id,
            right_event_id=right.source_event_id,
            left_bookmaker=left.bookmaker,
            right_bookmaker=right.bookmaker,
            confidence=confidence,
            score=min_similarity,
            reasons=reasons,
        )

    def _teams_similarity(self, left: EventOddsSnapshot, right: EventOddsSnapshot) -> float:
        direct = (
            self._similarity(left.home_team, right.home_team)
            + self._similarity(left.away_team, right.away_team)
        ) / 2
        swapped = (
            self._similarity(left.home_team, right.away_team)
            + self._similarity(left.away_team, right.home_team)
        ) / 2
        return max(direct, swapped)

    def _similarity(self, a: str, b: str) -> float:
        ka = self._canonical(a)
        kb = self._canonical(b)
        seq = SequenceMatcher(a=ka, b=kb).ratio()

        a_tokens = set(ka.split())
        b_tokens = set(kb.split())
        if not a_tokens or not b_tokens:
            return seq

        intersection = len(a_tokens & b_tokens)
        union = len(a_tokens | b_tokens)
        jaccard = intersection / union

        containment = max(intersection / len(a_tokens), intersection / len(b_tokens))
        return max(seq, jaccard, containment)

    @staticmethod
    def _canonical(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\b(fc|cf|sc|ac|cd|ca|club|deportivo|atletico|liga|primera|dimayor|colombia|a|los)\b", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _detect_shared_feed(self, events: list[EventOddsSnapshot], matches: list[MatchCandidate]) -> list[str]:
        event_index = {(e.bookmaker, e.source_event_id): e for e in events}
        warnings: list[str] = []
        for match in matches:
            left = event_index[(match.left_bookmaker, match.left_event_id)]
            right = event_index[(match.right_bookmaker, match.right_event_id)]
            same_market = left.market_type == right.market_type
            same_selection = self._canonical(left.selection) == self._canonical(right.selection)
            same_line = (left.line_value or "") == (right.line_value or "")
            same_odd = left.odds_decimal == right.odds_decimal
            if same_market and same_selection and same_line and same_odd:
                warnings.append(
                    f"Possible shared odds feed between {left.bookmaker} and {right.bookmaker} "
                    f"for {left.source_event_id}/{right.source_event_id}: identical market and odds"
                )
        return warnings
