"""Collector específico para Stake Colombia."""

from src.collectors.browser_collectors import CollectorStrategyHints, SmartBookmakerCollector


class Collector(SmartBookmakerCollector):
    strategy_hints = CollectorStrategyHints(
        sportsbook_label="Stake Colombia",
        json_target_hint=(
            "Stake suele usar APIs internas por deporte/torneo. Captura la llamada que retorna mercados prematch "
            "de fútbol con odds decimales y el identificador del evento."
        ),
        html_target_hint=(
            "Inspecciona filas de eventos y botones de cuotas; confirma selectores para detectar odd decimal "
            "sin depender de texto dinámico."
        ),
    )
