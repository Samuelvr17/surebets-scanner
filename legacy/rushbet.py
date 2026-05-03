"""Collector específico para RushBet Colombia."""

from src.collectors.browser_collectors import CollectorStrategyHints, SmartBookmakerCollector


class Collector(SmartBookmakerCollector):
    strategy_hints = CollectorStrategyHints(
        sportsbook_label="RushBet",
        json_target_hint=(
            "Entra a fútbol prematch y detecta llamada JSON con lista de fixtures y precios. "
            "Verifica si usa query params de competencia/país y copia la URL final más respuesta JSON."
        ),
        html_target_hint=(
            "Localiza en HTML los bloques de selección (1/X/2) y las cuotas. "
            "Anota atributos estables (id, data-testid, class persistente)."
        ),
    )
