"""Collector específico para Codere Colombia."""

from src.collectors.browser_collectors import CollectorStrategyHints, SmartBookmakerCollector


class Collector(SmartBookmakerCollector):
    strategy_hints = CollectorStrategyHints(
        sportsbook_label="Codere Colombia",
        json_target_hint=(
            "Filtra por XHR/Fetch y busca endpoint con competiciones + eventos + mercados de fútbol prematch. "
            "Copia URL exacta y JSON bruto para poblar placeholders."
        ),
        html_target_hint=(
            "En fallback, identifica los elementos de cuota por mercado principal (1X2). "
            "Guardar selectores que no cambien por partido."
        ),
    )
