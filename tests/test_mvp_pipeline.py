from decimal import Decimal
from pathlib import Path

from src.arbitrage.surebet_engine import detect_surebet
from src.matchers.event_matcher import match_events
from src.normalizers.odds_normalizer import normalize_snapshots
from src.pipeline import run_console_pipeline


def _odd(side, odd, family='1x2', line=None):
    return {"bookmaker":"a","sport":"soccer","league":"x","home_team":"Atletico Nacional FC","away_team":"America Cali","event_start_utc":"2026-05-10T20:00:00Z","market_family":family,"period":"ft","side_code":side,"line_value":line,"line_unit":"goals" if line else None,"selection":side,"odds_decimal":str(odd),"pulled_at_utc":"2026-05-03T10:00:00Z"}


def test_surebet_1x2_valida():
    legs = normalize_snapshots([_odd('home',3.6),_odd('draw',3.8),_odd('away',2.5)])
    assert detect_surebet(legs) is True


def test_no_surebet():
    legs = normalize_snapshots([_odd('home',2.0),_odd('draw',3.0),_odd('away',3.0)])
    assert detect_surebet(legs) is False


def test_mercado_incompleto():
    legs = normalize_snapshots([_odd('home',3.6),_odd('away',2.5)])
    assert detect_surebet(legs) is False


def test_over_under_lineas_diferentes():
    legs = normalize_snapshots([_odd('over',2.1,'totals','2.5'),_odd('under',2.1,'totals','3.5')])
    assert detect_surebet(legs) is False


def test_cuota_cambia_elimina_surebet():
    out = run_console_pipeline(Path('data/input_snapshots'),'snapshot_t0','snapshot_t1')
    assert out == []


def test_alias_equipos_fuzzy_matching_sin_igualdad_exacta():
    grouped = match_events(normalize_snapshots([_odd('home',2.0), {**_odd('away',2.0), 'home_team':'Atl. Nacional', 'away_team':'América de Cali'}]))
    assert len(grouped) == 1
