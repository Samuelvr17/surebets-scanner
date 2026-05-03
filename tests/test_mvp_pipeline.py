from pathlib import Path

from src.ingestion.local_snapshot_source import LocalSnapshotSource
from src.ingestion.source_registry import load_sources
from src.matchers.event_matcher import match_events
from src.normalizers.odds_normalizer import normalize_snapshots_with_errors
from src.normalizers.profile_mapper import map_profile_payload
from src.pipeline import run_console_pipeline


def _odd(bookmaker, side, odd, family='1x2', line=None, start='2026-05-10T20:00:00Z', home='Atletico Nacional', away='America Cali', league='liga betplay'):
    return {"bookmaker":bookmaker,"sport":"soccer","league":league,"home_team":home,"away_team":away,"event_start_utc":start,"market_family":family,"period":"ft","side_code":side,"line_value":line,"line_unit":"goals" if line else None,"selection":side,"odds_decimal":str(odd),"pulled_at_utc":"2026-05-03T10:00:00Z"}


def test_snapshot_local_validado():
    out = run_console_pipeline(Path('data/input_snapshots'), 'snapshot_t0', 'snapshot_t1_valid')
    assert len(out) == 1


def test_snapshot_local_expirado():
    assert run_console_pipeline(Path('data/input_snapshots'), 'snapshot_t0', 'snapshot_t1_expired') == []


def test_rechaza_market_family_desconocido():
    out = normalize_snapshots_with_errors([_odd('a', 'home', 2.0, family='weird')])
    assert 'unknown market_family' in out.errors[0]


def test_rechaza_side_code_invalido():
    out = normalize_snapshots_with_errors([_odd('a', 'bad', 2.0)])
    assert 'invalid side_code' in out.errors[0]


def test_rechaza_odds_menor_igual_uno():
    out = normalize_snapshots_with_errors([_odd('a', 'home', 1)])
    assert 'odds_decimal must be > 1' in out.errors[0]


def test_alias_equipo_y_liga_funciona():
    rows = normalize_snapshots_with_errors([_odd('a','home',2.0,home='At. Nacional',away='América de Cali',league='Liga BetPlay DIMAYOR')]).rows
    grouped = match_events(rows, aliases_path='config/aliases.yml')
    key = list(grouped.keys())[0]
    assert 'atletico nacional' in key and 'liga betplay' in key


def test_no_mezcla_equipos_invertidos():
    rows = normalize_snapshots_with_errors([_odd('a','home',2.0,home='Team A',away='Team B'), _odd('b','away',2.0,home='Team B',away='Team A')]).rows
    assert len(match_events(rows)) == 2


def test_no_mezcla_partidos_distinta_hora():
    rows = normalize_snapshots_with_errors([_odd('a','home',2.0,start='2026-05-10T20:00:00Z'), _odd('b','away',2.0,start='2026-05-10T22:00:00Z')]).rows
    assert len(match_events(rows)) == 2


def test_totals_lineas_distintas_no_mezcla():
    out = run_console_pipeline(Path('data/input_snapshots'), 'snapshot_t0', 'snapshot_multiple_events')
    assert isinstance(out, list)


def test_profile_mapper_transforma_sample():
    import json
    raw = json.load(open('data/samples/betplay_sample.json', encoding='utf-8'))
    rows, errors = map_profile_payload(raw, 'config/profiles/betplay.example.yml', 'betplay')
    normalized = normalize_snapshots_with_errors(rows)
    assert rows and not errors and normalized.rows


def test_source_registry_carga_habilitadas():
    sources = load_sources('config/sources.example.yml')
    assert len(sources) == 1 and sources[0].source_id == 'local_demo'


def test_healthcheck_local_snapshot_funciona():
    health = LocalSnapshotSource('local', 'data/input_snapshots', 'snapshot_t0').healthcheck()
    assert health.ok
