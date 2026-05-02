"""Herramienta para guardar sesión manual de una casa y reutilizarla."""

from __future__ import annotations

from pathlib import Path

from src.config.settings import AppConfig


def save_manual_session_state(app_config: AppConfig, bookmaker: str) -> Path:
    """Abre navegador visible para login manual y guarda storage_state.

    Requiere `playwright` instalado en el entorno del usuario.
    """
    if bookmaker not in app_config.bookmakers:
        valid = ", ".join(sorted(app_config.bookmakers.keys()))
        raise ValueError(f"Bookmaker inválido: {bookmaker}. Opciones: {valid}")

    bookmaker_cfg = app_config.bookmakers[bookmaker]
    storage_path = bookmaker_cfg.session_state_file
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Playwright no está instalado. Ejecuta: pip install playwright && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(bookmaker_cfg.base_url, wait_until="domcontentloaded")
        print("\nInicia sesión manualmente en la web abierta.")
        input("Cuando confirmes que el login quedó activo, presiona ENTER aquí para guardar la sesión... ")
        context.storage_state(path=str(storage_path))
        browser.close()

    return storage_path
