"""Collectores browser-first para casas colombianas (prematch fútbol)."""

from __future__ import annotations

from typing import Any

from src.collectors.base import BaseBookmakerCollector


class PlaceholderXHRCollector(BaseBookmakerCollector):
    """Collector temporal hasta inyectar URL/JSON reales capturados manualmente.

    Flujo esperado (manual):
    1) Abrir casa en Chrome visible con sesión iniciada.
    2) F12 -> Network -> Fetch/XHR.
    3) Copiar URL real y JSON respuesta de mercados prematch.
    4) Reemplazar placeholders en config/env y volver a ejecutar.
    """

    def fetch_raw_payloads(self) -> list[dict[str, Any]]:
        if self.config.xhr_url_placeholder.startswith("__REEMPLAZAR"):
            raise RuntimeError(
                "Falta URL XHR real. Completa <BOOKMAKER>_XHR_URL con la URL capturada manualmente."
            )

        if self.config.json_sample_placeholder.startswith("__REEMPLAZAR"):
            raise RuntimeError(
                "Falta JSON de ejemplo real. Completa <BOOKMAKER>_JSON_SAMPLE con el JSON capturado."
            )

        return [
            {
                "event_id": "manual-placeholder-event",
                "xhr_url": self.config.xhr_url_placeholder,
                "raw_json": self.config.json_sample_placeholder,
                "note": "placeholder hasta integrar interceptación automática por Playwright",
            }
        ]
