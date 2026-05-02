"""Collectores browser-first para casas colombianas (prematch fútbol)."""

from __future__ import annotations

import json
import logging
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

from src.collectors.base import BaseBookmakerCollector

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CollectorStrategyHints:
    sportsbook_label: str
    json_target_hint: str
    html_target_hint: str


class _OddsTextExtractor(HTMLParser):
    """Extractor básico de texto visible que parece cuota decimal."""

    def __init__(self) -> None:
        super().__init__()
        self.odds: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip().replace(",", ".")
        if not value:
            return
        try:
            maybe_odd = float(value)
        except ValueError:
            return
        if 1.01 <= maybe_odd <= 100.0:
            self.odds.append(value)


class SmartBookmakerCollector(BaseBookmakerCollector):
    """Collector inteligente con prioridad JSON y fallback HTML + backoff."""

    strategy_hints = CollectorStrategyHints(
        sportsbook_label="generic",
        json_target_hint="Buscar endpoint XHR/Fetch con mercados prematch de fútbol.",
        html_target_hint="Identificar nodos HTML donde se renderizan cuotas 1X2.",
    )

    def fetch_raw_payloads(self) -> list[dict[str, Any]]:
        json_method = self._try_json_endpoint()
        if json_method is not None:
            return [json_method]

        html_method = self._try_html_fallback()
        if html_method is not None:
            return [html_method]

        raise RuntimeError(
            f"No se pudo extraer data en {self.config.bookmaker}. "
            "Completa placeholders y valida DevTools según instrucciones del colector."
        )

    def _try_json_endpoint(self) -> dict[str, Any] | None:
        if self.config.xhr_url_placeholder.startswith("__REEMPLAZAR"):
            logger.warning(
                "[%s] JSON path incompleto. Inspeccionar DevTools: %s",
                self.config.bookmaker,
                self.strategy_hints.json_target_hint,
            )
            return None

        response_text = self._get_with_backoff(self.config.xhr_url_placeholder)
        if response_text is None:
            return None

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("[%s] XHR respondió pero no devolvió JSON válido.", self.config.bookmaker)
            return None

        return {
            "event_id": "json-endpoint-placeholder-event",
            "collection_method": "json_xhr",
            "bookmaker": self.strategy_hints.sportsbook_label,
            "xhr_url": self.config.xhr_url_placeholder,
            "raw_json": parsed,
            "devtools_note": self.strategy_hints.json_target_hint,
        }

    def _try_html_fallback(self) -> dict[str, Any] | None:
        html = self._get_with_backoff(self.config.sport_section_url)
        if html is None:
            return None

        parser = _OddsTextExtractor()
        parser.feed(html)
        if not parser.odds:
            logger.warning(
                "[%s] HTML sin cuotas detectables. Revisar selector visual. %s",
                self.config.bookmaker,
                self.strategy_hints.html_target_hint,
            )
            return None

        return {
            "event_id": "html-fallback-placeholder-event",
            "collection_method": "html_fallback",
            "bookmaker": self.strategy_hints.sportsbook_label,
            "sport_url": self.config.sport_section_url,
            "detected_odds": parser.odds[:100],
            "devtools_note": self.strategy_hints.html_target_hint,
        }

    def _get_with_backoff(self, url: str) -> str | None:
        max_attempts = 4
        base_delay = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Personal Odds Observer)",
                        "Accept": "application/json,text/html,*/*",
                    },
                )
                with urllib.request.urlopen(request, timeout=max(self.runtime.timeout_ms / 1000, 5)) as response:
                    return response.read().decode("utf-8", errors="replace")
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                if attempt == max_attempts:
                    logger.error("[%s] Error persistente contra %s: %s", self.config.bookmaker, url, exc)
                    return None
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.35)
                logger.warning(
                    "[%s] Error tentativa %s/%s contra %s. Backoff %.2fs. Error: %s",
                    self.config.bookmaker,
                    attempt,
                    max_attempts,
                    url,
                    delay,
                    exc,
                )
                time.sleep(delay)
        return None
