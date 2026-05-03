"""Variables de entorno y parámetros globales de ejecución local."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final


BOOKMAKERS: Final[tuple[str, ...]] = (
    "betplay",
    "rushbet",
    "stake_colombia",
    "codere_colombia",
    "sportium_colombia",
)


@dataclass(frozen=True, slots=True)
class CollectorRuntimeConfig:
    """Configuración común que todos los collectores deben recibir."""

    run_id: str
    headless: bool
    timeout_ms: int
    prematch_only: bool
    football_only: bool
    session_store_dir: Path
    raw_dump_dir: Path
    collector_version: str


@dataclass(frozen=True, slots=True)
class BookmakerCollectorConfig:
    """Configuración individual por casa para mantener contrato homogéneo."""

    bookmaker: str
    enabled: bool
    base_url: str
    sport_section_url: str
    session_state_file: Path
    xhr_url_placeholder: str
    json_sample_placeholder: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    runtime: CollectorRuntimeConfig
    bookmakers: dict[str, BookmakerCollectorConfig]


def _as_bool(value: str, default: bool) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_app_config() -> AppConfig:
    session_dir = Path(os.getenv("SESSION_STORE_DIR", "data/sessions"))
    raw_dir = Path(os.getenv("RAW_DUMP_DIR", "data/raw_captures"))

    runtime = CollectorRuntimeConfig(
        run_id=os.getenv("RUN_ID", "local-dev"),
        headless=_as_bool(os.getenv("COLLECTOR_HEADLESS", "false"), default=False),
        timeout_ms=int(os.getenv("COLLECTOR_TIMEOUT_MS", "45000")),
        prematch_only=True,
        football_only=True,
        session_store_dir=session_dir,
        raw_dump_dir=raw_dir,
        collector_version=os.getenv("COLLECTOR_VERSION", "0.1.0"),
    )

    bookmakers: dict[str, BookmakerCollectorConfig] = {}
    for bookmaker in BOOKMAKERS:
        prefix = bookmaker.upper()
        bookmakers[bookmaker] = BookmakerCollectorConfig(
            bookmaker=bookmaker,
            enabled=_as_bool(os.getenv(f"{prefix}_ENABLED", "true"), default=True),
            base_url=os.getenv(f"{prefix}_BASE_URL", f"https://{bookmaker}.com"),
            sport_section_url=os.getenv(
                f"{prefix}_SPORT_SECTION_URL",
                f"https://{bookmaker}.com/deportes/futbol",
            ),
            session_state_file=session_dir / f"{bookmaker}_state.json",
            xhr_url_placeholder=os.getenv(
                f"{prefix}_XHR_URL", "__REEMPLAZAR_URL_XHR_REAL__"
            ),
            json_sample_placeholder=os.getenv(
                f"{prefix}_JSON_SAMPLE", "__REEMPLAZAR_JSON_REAL__"
            ),
        )

    return AppConfig(runtime=runtime, bookmakers=bookmakers)
