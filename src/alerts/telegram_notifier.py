"""Notificador de alertas (placeholder) con gate de estado validado."""

from __future__ import annotations

from src.models.schemas import SurebetOpportunity


def should_send_alert(opportunity: SurebetOpportunity) -> bool:
    """Solo se alerta cuando la oportunidad ya pasó revalidación."""
    return opportunity.status == "validated"
