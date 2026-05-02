"""Pruebas base de estructura/contratos para módulos de captura."""

from src.config.settings import build_app_config
from src.pipeline import run_capture_pipeline


def test_all_bookmakers_are_present() -> None:
    config = build_app_config()
    assert len(config.bookmakers) == 5


def test_collectors_fail_in_controlled_way_with_placeholders() -> None:
    config = build_app_config()
    results = run_capture_pipeline(config)

    assert len(results) == 5
    for result in results:
        assert result.bookmaker
        assert result.errors  # placeholder sin URL/JSON real debe fallar controlado
