"""Collector específico para Sportium Colombia."""

from src.collectors.browser_collectors import CollectorStrategyHints, SmartBookmakerCollector


class Collector(SmartBookmakerCollector):
    strategy_hints = CollectorStrategyHints(
        sportsbook_label="Sportium Colombia",
        json_target_hint=(
            "En DevTools identifica llamada XHR/Fetch de fútbol prematch y confirma campos de cuotas/evento. "
            "Usar frecuencia baja de consulta y respetar uso personal observacional según TOS."
        ),
        html_target_hint=(
            "Si JSON falla, inspecciona contenedores de odds renderizados en la página de deportes; "
            "prioriza selectores estables y evita scraping agresivo."
        ),
    )
