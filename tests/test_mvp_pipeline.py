from pathlib import Path

from src.arbitrage.surebet_engine import detect_surebet
from src.matchers.event_matcher import match_events
from src.normalizers.odds_normalizer import normalize_snapshots
from src.pipeline import run_console_pipeline


def _odd(bookmaker, side, odd, family='1x2', line=None, start='2026-05-10T20:00:00Z', home='Atletico Nacional', away='America Cali'):
    return {"bookmaker":bookmaker,"sport":"soccer","league":"x","home_team":home,"away_team":away,"event_start_utc":start,"market_family":family,"period":"ft","side_code":side,"line_value":line,"line_unit":"goals" if line else None,"selection":side,"odds_decimal":str(odd),"pulled_at_utc":"2026-05-03T10:00:00Z"}


def test_pipeline_imprime_surebet_validada():
    out = run_console_pipeline(Path('data/input_snapshots'), 'snapshot_t0', 'snapshot_t1_valid')
    assert len(out) == 1
    assert 'revalidación: validated' in out[0]


def test_pipeline_no_imprime_si_expira():
    out = run_console_pipeline(Path('data/input_snapshots'), 'snapshot_t0', 'snapshot_t1_expired')
    assert out == []


def test_no_detecta_surebet_una_sola_casa():
    legs = normalize_snapshots([_odd('a', 'home', 3.8), _odd('a', 'draw', 4.2), _odd('a', 'away', 2.7)])
    res = detect_surebet(legs, 'evt')
    assert not res.is_surebet
    assert res.reason == 'single_bookmaker'


def test_no_mezcla_partidos_misma_pareja_distinta_hora():
    rows = normalize_snapshots([_odd('a', 'home', 2.0, start='2026-05-10T20:00:00Z'), _odd('b', 'away', 2.0, start='2026-05-10T22:00:00Z')])
    grouped = match_events(rows)
    assert len(grouped) == 2


def test_no_mezcla_over_under_lineas_diferentes():
    rows = normalize_snapshots([_odd('a','over',2.1,'totals','2.5'),_odd('b','under',2.1,'totals','3.5')])
    res = detect_surebet(rows, 'evt')
    assert not res.is_surebet


def test_no_acepta_equipos_invertidos_sin_remap():
    rows = normalize_snapshots([_odd('a','home',2.0,home='Team A',away='Team B'), _odd('b','away',2.0,home='Team B',away='Team A')])
    grouped = match_events(rows)
    assert len(grouped) == 2


def test_output_contiene_bookmaker_selection_odds_roi():
    out = run_console_pipeline(Path('data/input_snapshots'), 'snapshot_t0', 'snapshot_t1_valid')
    row = out[0]
    assert 'pata:' in row
    assert 'ROI:' in row
    assert 'betplay' in row
