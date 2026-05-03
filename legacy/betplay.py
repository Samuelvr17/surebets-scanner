"""Collector específico para BetPlay Colombia."""

from src.collectors.browser_collectors import CollectorStrategyHints, SmartBookmakerCollector


class Collector(SmartBookmakerCollector):
    strategy_hints = CollectorStrategyHints(
        sportsbook_label="BetPlay",
        json_target_hint=(
            "En DevTools filtra Fetch/XHR y ubica requests con payload de eventos + mercados + odds "
            "(ej. 1X2, over/under) dentro de la sección fútbol prematch. "
            "Copiar URL completa y JSON de respuesta."
        ),
        html_target_hint=(
            "Inspecciona cards de partido y valida clases/data-attributes del precio decimal de cuota. "
            "Identifica dónde aparece local/empate/visitante para mapearlo luego."
        ),
    )
