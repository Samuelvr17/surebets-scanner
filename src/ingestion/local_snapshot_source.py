from __future__ import annotations

import json
from pathlib import Path

from src.ingestion.base import OddsSource
from src.models.schemas import SourceHealth


class LocalSnapshotSource(OddsSource):
    source_type = 'local_snapshot'

    def __init__(self, source_id: str, input_dir: str, snapshot_name: str) -> None:
        self.source_id = source_id
        self.input_dir = Path(input_dir)
        self.snapshot_name = snapshot_name

    def fetch_snapshot(self) -> list[dict]:
        with (self.input_dir / f'{self.snapshot_name}.json').open(encoding='utf-8') as f:
            return json.load(f)

    def healthcheck(self) -> SourceHealth:
        path = self.input_dir / f'{self.snapshot_name}.json'
        return SourceHealth(self.source_id, self.source_type, path.exists(), f'path={path}')
