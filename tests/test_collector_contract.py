"""Pruebas de contrato base para collectores."""

from __future__ import annotations

import json
from pathlib import Path

from src.collectors.base import BaseBookmakerCollector
from src.collectors.session_manager import save_manual_session_state
from src.config.settings import AppConfig, BookmakerCollectorConfig, CollectorRuntimeConfig


class _FakeCollector(BaseBookmakerCollector):
    def __init__(self, *args, payloads=None, should_raise=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._payloads = payloads or []
        self._should_raise = should_raise

    def fetch_raw_payloads(self):
        if self._should_raise:
            raise RuntimeError("boom")
        return self._payloads


def _runtime(tmp_path: Path) -> CollectorRuntimeConfig:
    return CollectorRuntimeConfig(
        run_id="test-run",
        headless=True,
        timeout_ms=2000,
        prematch_only=True,
        football_only=True,
        session_store_dir=tmp_path / "sessions",
        raw_dump_dir=tmp_path / "raw",
        collector_version="test",
    )


def _bookmaker_cfg(tmp_path: Path, bookmaker: str = "betplay") -> BookmakerCollectorConfig:
    return BookmakerCollectorConfig(
        bookmaker=bookmaker,
        enabled=True,
        base_url="https://example.com",
        sport_section_url="https://example.com/futbol",
        session_state_file=tmp_path / "sessions" / f"{bookmaker}_state.json",
        xhr_url_placeholder="https://example.com/xhr",
        json_sample_placeholder="{}",
    )


def test_raw_payload_is_saved_to_disk(tmp_path: Path) -> None:
    collector = _FakeCollector(
        runtime=_runtime(tmp_path),
        bookmaker_config=_bookmaker_cfg(tmp_path),
        payloads=[{"event_id": "e-1", "odd": 2.15}],
    )

    result = collector.collect()

    assert len(result.errors) == 0
    assert len(result.captures) == 1
    capture = result.captures[0]
    assert capture.raw_file_path.exists()
    assert json.loads(capture.raw_file_path.read_text(encoding="utf-8")) == {"event_id": "e-1", "odd": 2.15}


def test_collector_does_not_fail_silently(tmp_path: Path) -> None:
    collector = _FakeCollector(
        runtime=_runtime(tmp_path),
        bookmaker_config=_bookmaker_cfg(tmp_path),
        should_raise=True,
    )

    result = collector.collect()

    assert result.errors
    assert "failed safely" in result.errors[0]


def test_deduplicates_same_payload(tmp_path: Path) -> None:
    repeated = {"event_id": "same", "odd": 1.83}
    collector = _FakeCollector(
        runtime=_runtime(tmp_path),
        bookmaker_config=_bookmaker_cfg(tmp_path),
        payloads=[repeated, repeated],
    )

    result = collector.collect()

    assert len(result.captures) == 1
    assert result.duplicates_discarded == 1


def test_save_session_rejects_unknown_bookmaker(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    known = _bookmaker_cfg(tmp_path, bookmaker="betplay")
    config = AppConfig(runtime=runtime, bookmakers={"betplay": known})

    try:
        save_manual_session_state(config, "desconocido")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Bookmaker inválido" in str(exc)
