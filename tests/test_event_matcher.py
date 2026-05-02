from datetime import datetime, timezone
from decimal import Decimal

from src.matchers.event_matcher import EventMatcher, EventOddsSnapshot


def _event(**kwargs: object) -> EventOddsSnapshot:
    base = dict(
        bookmaker="betplay",
        source_event_id="evt-1",
        sport="futbol",
        league="Liga BetPlay Dimayor",
        home_team="Atlético Nacional",
        away_team="América de Cali",
        event_start_utc=datetime(2026, 5, 4, 1, 0, tzinfo=timezone.utc),
        market_type="MATCH_RESULT_1X2",
        selection="Home",
        line_value=None,
        odds_decimal=Decimal("2.20"),
    )
    base.update(kwargs)
    return EventOddsSnapshot(**base)


def test_high_confidence_with_colombian_names_swapped_home_away() -> None:
    matcher = EventMatcher(max_start_diff_minutes=5)
    left = _event()
    right = _event(
        bookmaker="rushbet",
        source_event_id="evt-rush-44",
        league="Liga Betplay",
        home_team="America Cali",
        away_team="Atletico Nacional FC",
        event_start_utc=datetime(2026, 5, 4, 1, 3, tzinfo=timezone.utc),
    )

    result = matcher.match([left, right])

    assert len(result.auto_matched) == 1
    assert len(result.manual_review) == 0
    assert result.auto_matched[0].confidence == "high"


def test_low_confidence_goes_to_manual_review() -> None:
    matcher = EventMatcher(max_start_diff_minutes=5, high_similarity_threshold=0.98, low_similarity_threshold=0.80)
    left = _event(home_team="Independiente Santa Fe", away_team="Millonarios")
    right = _event(
        bookmaker="stake",
        source_event_id="evt-stake-10",
        league="Liga Betplay Colombia",
        home_team="Santa Fe Bogota",
        away_team="Los Millonarios",
        event_start_utc=datetime(2026, 5, 4, 1, 2, tzinfo=timezone.utc),
    )

    result = matcher.match([left, right])

    assert len(result.auto_matched) == 0
    assert len(result.manual_review) == 1
    assert result.manual_review[0].confidence == "low"


def test_different_kickoff_time_is_rejected() -> None:
    matcher = EventMatcher(max_start_diff_minutes=5)
    left = _event()
    right = _event(
        bookmaker="codere",
        source_event_id="evt-codere-9",
        event_start_utc=datetime(2026, 5, 4, 1, 20, tzinfo=timezone.utc),
    )

    result = matcher.match([left, right])

    assert len(result.auto_matched) == 0
    assert len(result.manual_review) == 0


def test_detects_possible_shared_feed_when_odds_are_identical() -> None:
    matcher = EventMatcher(max_start_diff_minutes=5)
    left = _event(bookmaker="betplay", source_event_id="evt-bp-7", odds_decimal=Decimal("1.91"))
    right = _event(bookmaker="sportium", source_event_id="evt-sp-7", odds_decimal=Decimal("1.91"))

    result = matcher.match([left, right])

    assert len(result.auto_matched) == 1
    assert len(result.shared_feed_warnings) == 1
    assert "Possible shared odds feed" in result.shared_feed_warnings[0]
