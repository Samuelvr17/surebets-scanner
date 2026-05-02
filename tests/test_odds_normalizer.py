from decimal import Decimal

from src.normalizers.odds_normalizer import OddsNormalizer


def test_normalizes_aliases_market_time_and_decimal_odds() -> None:
    normalizer = OddsNormalizer()
    payload = {
        "home_team": "Atl. Nacional",
        "away_team": "América de Cali",
        "league": "Liga BetPlay",
        "event_start": "2026-05-02T20:00:00-05:00",
        "odds": [
            {"market": "1X2", "selection": "Home", "odds": "+150"},
            {"market": "Asian Handicap", "selection": "Away", "line": "+0.5", "odds": "5/2"},
        ],
    }

    result = normalizer.normalize_payload("betplay", "evt-1", payload)

    assert len(result.discarded) == 0
    assert len(result.normalized) == 2
    assert result.normalized[0].home_team == "Atlético Nacional"
    assert result.normalized[0].league == "Colombia - Categoría Primera A"
    assert result.normalized[0].event_start_utc.isoformat() == "2026-05-03T01:00:00+00:00"
    assert result.normalized[0].odds_decimal == Decimal("2.5")
    assert result.normalized[1].odds_decimal == Decimal("3.5")


def test_fallback_heuristic_works_without_full_alias_coverage() -> None:
    normalizer = OddsNormalizer()
    payload = {
        "home_team": "Manchester Utd",
        "away_team": "Tottenham Hotspur FC",
        "league": "England Premier League",
        "event_start": "2026-05-02T20:00:00-05:00",
        "odds": [{"market": "1X2", "selection": "Home", "odds": "2.1"}],
    }

    result = normalizer.normalize_payload("bookx", "evt-heuristic", payload)

    assert len(result.discarded) == 0
    assert len(result.normalized) == 1
    record = result.normalized[0]
    assert record.home_team_key == "manchester united"
    assert record.away_team_key == "hotspur tottenham"
    assert record.league_key == "england premier"


def test_discards_ambiguous_market_instead_of_guessing() -> None:
    normalizer = OddsNormalizer()
    payload = {
        "home_team": "Atlético Nacional",
        "away_team": "América de Cali",
        "league": "Liga BetPlay",
        "event_start": "2026-05-02T20:00:00-05:00",
        "odds": [{"market": "Special Combo", "selection": "Home or Over", "odds": "2.0"}],
    }

    result = normalizer.normalize_payload("rushbet", "evt-2", payload)

    assert len(result.normalized) == 0
    assert len(result.discarded) == 1
    assert result.discarded[0].reason == "unknown_or_ambiguous_market"
