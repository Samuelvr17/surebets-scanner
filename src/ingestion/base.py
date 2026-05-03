from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.schemas import SourceHealth, SourceType


class OddsSource(ABC):
    source_id: str
    source_type: SourceType

    @abstractmethod
    def fetch_snapshot(self) -> list[dict]: ...

    @abstractmethod
    def healthcheck(self) -> SourceHealth: ...
