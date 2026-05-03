from __future__ import annotations

from src.ingestion.base import OddsSource
from src.models.schemas import SourceHealth


class AuthorizedAPISource(OddsSource):
    source_type = 'authorized_api'

    def __init__(self, source_id: str, base_url: str, api_key_env: str | None = None) -> None:
        self.source_id = source_id
        self.base_url = base_url
        self.api_key_env = api_key_env

    def fetch_snapshot(self) -> list[dict]:
        return []

    def healthcheck(self) -> SourceHealth:
        ok = bool(self.base_url)
        return SourceHealth(self.source_id, self.source_type, ok, 'stub: implement provider call')
