"""Contrato base para collectors que extraen cuotas prematch de fútbol."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from src.config.settings import BookmakerCollectorConfig, CollectorRuntimeConfig

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class CaptureRecord:
    bookmaker: str
    source_event_id: str
    fetched_at_utc: datetime
    payload: dict[str, Any]
    payload_json: str
    payload_hash: str
    raw_file_path: Path
    collector_version: str


@dataclass(slots=True)
class CollectorResult:
    bookmaker: str
    started_at_utc: datetime
    finished_at_utc: datetime
    captures: list[CaptureRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class OddsCollector(Protocol):
    def collect(self) -> CollectorResult: ...


class BaseBookmakerCollector:
    """Lógica compartida: contrato homogéneo, resiliencia y dumps crudos."""

    def __init__(
        self,
        runtime: CollectorRuntimeConfig,
        bookmaker_config: BookmakerCollectorConfig,
    ) -> None:
        self.runtime = runtime
        self.config = bookmaker_config
        self.runtime.raw_dump_dir.mkdir(parents=True, exist_ok=True)

    def collect(self) -> CollectorResult:
        started = utc_now()
        result = CollectorResult(
            bookmaker=self.config.bookmaker,
            started_at_utc=started,
            finished_at_utc=started,
        )
        try:
            payloads = self.fetch_raw_payloads()
            for payload in payloads:
                result.captures.append(self._build_capture(payload=payload))
        except Exception as exc:  # nosec B110
            message = f"{self.config.bookmaker} collector failed safely: {exc}"
            logger.exception(message)
            result.errors.append(message)
        finally:
            result.finished_at_utc = utc_now()
        return result

    def fetch_raw_payloads(self) -> list[dict[str, Any]]:
        """Implementar por casa: devolver lista de payloads JSON crudos."""
        raise NotImplementedError

    def _build_capture(self, payload: dict[str, Any]) -> CaptureRecord:
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        fetched_at = utc_now()
        source_event_id = str(payload.get("event_id", "unknown-event"))
        raw_file_path = self._dump_raw_payload(payload_hash=payload_hash, payload_json=payload_json)
        return CaptureRecord(
            bookmaker=self.config.bookmaker,
            source_event_id=source_event_id,
            fetched_at_utc=fetched_at,
            payload=payload,
            payload_json=payload_json,
            payload_hash=payload_hash,
            raw_file_path=raw_file_path,
            collector_version=self.runtime.collector_version,
        )

    def _dump_raw_payload(self, payload_hash: str, payload_json: str) -> Path:
        bookmaker_dir = self.runtime.raw_dump_dir / self.config.bookmaker
        bookmaker_dir.mkdir(parents=True, exist_ok=True)
        filepath = bookmaker_dir / f"{utc_now().strftime('%Y%m%dT%H%M%S')}_{payload_hash[:12]}.json"
        filepath.write_text(payload_json, encoding="utf-8")
        return filepath
