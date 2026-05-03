from __future__ import annotations

from src.ingestion.base import OddsSource
from src.models.schemas import SourceHealth


class BookmakerSource(OddsSource):
    source_type = 'bookmaker_adapter'

    def __init__(self, source_id: str, bookmaker: str, adapter_profile: str) -> None:
        self.source_id = source_id
        self.bookmaker = bookmaker
        self.adapter_profile = adapter_profile

    def fetch_snapshot(self) -> list[dict]:
        return []

    def healthcheck(self) -> SourceHealth:
        return SourceHealth(self.source_id, self.source_type, True, f'stub adapter for {self.bookmaker}')
